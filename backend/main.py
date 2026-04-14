from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from collections import defaultdict
import os, shutil, uuid, struct, whisper
from transformers import pipeline

import database_model
from table import Lecture

# ════════════════════════════════════════════════════════════
#  APP
# ════════════════════════════════════════════════════════════
app = FastAPI(title="SmartClassroom Auto Notes API", version="0.6.0")

# ── CORS ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── DB ───────────────────────────────────────────────────────
database_model.Base.metadata.create_all(bind=database_model.engine)

def get_db():
    db = database_model.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── Temp folder ──────────────────────────────────────────────
TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# ── In-memory chunk session store ────────────────────────────
chunk_sessions: dict = defaultdict(lambda: {
    "transcripts":  [],
    "title":        "",
    "subject":      "",
    "language":     "ta",
    "initial_prompt": ""
})

# ════════════════════════════════════════════════════════════
#  LOAD AI MODELS
# ════════════════════════════════════════════════════════════
print("[STARTUP] Loading Whisper small model...")
whisper_model = whisper.load_model("small")

print("[STARTUP] Loading grammar corrector...")
grammar_pipe = pipeline(
    "text2text-generation",
    model="prithivida/grammar_error_correcter_v1"
)

print("[STARTUP] Loading summarizer...")
summarizer = pipeline(
    "summarization",
    model="facebook/bart-large-cnn"
)

print("[STARTUP] ✅ All models loaded!")

# ════════════════════════════════════════════════════════════
#  SCHEMAS
# ════════════════════════════════════════════════════════════
class LectureUpdate(BaseModel):
    subject:    Optional[str] = None
    title:      Optional[str] = None
    transcript: Optional[str] = None
    summary:    Optional[str] = None


class LectureResponse(BaseModel):
    id:         int
    subject:    str
    title:      str
    transcript: str
    summary:    str
    created_at: str

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj: Lecture):
        return cls(
            id=obj.id,
            subject=obj.subject,
            title=obj.title,
            transcript=obj.transcript,
            summary=obj.summary,
            created_at=obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
        )

# ════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════
def build_wav_header(pcm_size: int, sample_rate: int,
                     channels: int, bits_per_sample: int) -> bytes:
    byte_rate   = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    return struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + pcm_size, b"WAVE",
        b"fmt ", 16, 1, channels, sample_rate,
        byte_rate, block_align, bits_per_sample,
        b"data", pcm_size
    )


def transcribe_audio(path: str, language: str = "ta",
                     initial_prompt: str = "") -> str:
    result = whisper_model.transcribe(
        path,
        task="translate",
        language=language,
        fp16=False,
        verbose=False,
        initial_prompt=initial_prompt if initial_prompt.strip() else None
    )
    return result["text"].strip()


def correct_and_summarize(raw_text: str):
    print(f"[NLP] Correcting grammar ({len(raw_text)} chars)...")

    # prithivida model uses "gec:" prefix
    corrected = grammar_pipe(
        f"gec: {raw_text}",
        max_length=512,
        truncation=True
    )[0]["generated_text"]

    print("[NLP] Summarizing...")
    summary = summarizer(
        corrected,
        max_length=150,
        min_length=40,
        do_sample=False
    )[0]["summary_text"]

    return corrected, summary


def save_to_db(title, subject, transcript, summary, db) -> Lecture:
    lecture = Lecture(
        title=title,
        subject=subject,
        transcript=transcript,
        summary=summary
    )
    db.add(lecture)
    db.commit()
    db.refresh(lecture)
    print(f"[DB] ✅ Saved lecture ID: {lecture.id}")
    return lecture


def process_audio_file(temp_path, title, subject,
                        language, initial_prompt, db) -> LectureResponse:
    try:
        print(f"[PIPELINE] Transcribing | lang={language}")
        raw_text = transcribe_audio(temp_path, language, initial_prompt)
        print(f"[PIPELINE] Raw: {raw_text[:100]}...")
        corrected, summary = correct_and_summarize(raw_text)
        lecture = save_to_db(title, subject, corrected, summary, db)
        return LectureResponse.from_orm(lecture)
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Processing error: {str(e)}")

# ════════════════════════════════════════════════════════════
#  ROUTES
# ════════════════════════════════════════════════════════════

# ── Health / Ping ─────────────────────────────────────────────
@app.get("/")
def health():
    return {
        "status":  "ok",
        "message": "SmartClassroom API v0.6.0 running",
        "routes": {
            "POST /uploadfile/":  "Manual WAV upload",
            "POST /uploadraw/":   "ESP32 single PCM blob",
            "POST /uploadchunk/": "ESP32 chunked PCM",
            "POST /debug_audio/": "Audio amplitude check",
            "GET  /lectures/":    "All lectures",
            "GET  /lectures/{id}":"Single lecture",
            "PATCH  /lectures/{id}": "Edit lecture",
            "DELETE /lectures/{id}": "Delete lecture"
        }
    }

# ── Route 1 : Manual WAV upload ───────────────────────────────
@app.post("/uploadfile/", response_model=LectureResponse, tags=["Manual"])
async def upload_file(
    file:           UploadFile = File(...),
    title:          str        = Form(...),
    subject:        str        = Form(...),
    language:       str        = Form(default="ta"),
    initial_prompt: str        = Form(default=""),
    db:             Session    = Depends(get_db)
):
    if not file.filename.lower().endswith(".wav"):
        raise HTTPException(400, "Only WAV files accepted")

    temp_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}.wav")
    try:
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        print(f"[uploadfile] {os.path.getsize(temp_path)}B | {title}")
        return process_audio_file(temp_path, title, subject,
                                  language, initial_prompt, db)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# ── Route 2 : Raw PCM single shot ─────────────────────────────
@app.post("/uploadraw/", response_model=LectureResponse, tags=["Embedded"])
async def upload_raw(
    file:            UploadFile = File(...),
    title:           str        = Form(...),
    subject:         str        = Form(...),
    language:        str        = Form(default="ta"),
    initial_prompt:  str        = Form(default=""),
    sample_rate:     int        = Form(default=16000),
    channels:        int        = Form(default=1),
    bits_per_sample: int        = Form(default=16),
    db:              Session    = Depends(get_db)
):
    pcm_data = await file.read()
    if len(pcm_data) == 0:
        raise HTTPException(400, "Empty audio received")

    wav_bytes = build_wav_header(
        len(pcm_data), sample_rate, channels, bits_per_sample
    ) + pcm_data

    temp_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}.wav")
    try:
        with open(temp_path, "wb") as f:
            f.write(wav_bytes)
        duration = len(pcm_data) / sample_rate / channels / (bits_per_sample // 8)
        print(f"[uploadraw] {len(pcm_data)}B | {duration:.1f}s | {title}")
        return process_audio_file(temp_path, title, subject,
                                  language, initial_prompt, db)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# ── Route 3 : Chunked PCM from ESP32 ──────────────────────────
@app.post("/uploadchunk/", tags=["Embedded"])
async def upload_chunk(
    file:            UploadFile = File(...),
    session_id:      str        = Form(...),
    chunk_index:     int        = Form(...),
    is_last:         str        = Form(...),
    title:           str        = Form(...),
    subject:         str        = Form(...),
    language:        str        = Form(default="ta"),
    initial_prompt:  str        = Form(default=""),
    sample_rate:     int        = Form(default=16000),
    channels:        int        = Form(default=1),
    bits_per_sample: int        = Form(default=16),
    db:              Session    = Depends(get_db)
):
    pcm_data = await file.read()
    if len(pcm_data) == 0:
        raise HTTPException(400, "Empty chunk received")

    print(f"[CHUNK] session={session_id} idx={chunk_index} "
          f"size={len(pcm_data)}B is_last={is_last} lang={language}")

    wav_bytes = build_wav_header(
        len(pcm_data), sample_rate, channels, bits_per_sample
    ) + pcm_data

    temp_path = os.path.join(TEMP_DIR, f"{session_id}_chunk{chunk_index}.wav")
    try:
        with open(temp_path, "wb") as f:
            f.write(wav_bytes)
        chunk_transcript = transcribe_audio(temp_path, language, initial_prompt)
        print(f"[CHUNK] Transcript: {chunk_transcript[:80]}...")
    except Exception as e:
        raise HTTPException(500, f"Transcription error: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    chunk_sessions[session_id]["transcripts"].append((chunk_index, chunk_transcript))
    chunk_sessions[session_id]["title"]          = title
    chunk_sessions[session_id]["subject"]        = subject
    chunk_sessions[session_id]["language"]       = language
    chunk_sessions[session_id]["initial_prompt"] = initial_prompt

    if is_last.lower() != "true":
        return {
            "status":      "chunk_received",
            "chunk_index": chunk_index,
            "transcript":  chunk_transcript,
            "message":     f"Chunk {chunk_index} OK"
        }

    print(f"[CHUNK] Last chunk — finalizing session {session_id}...")

    sorted_chunks   = sorted(
        chunk_sessions[session_id]["transcripts"], key=lambda x: x[0]
    )
    full_transcript = " ".join([t for _, t in sorted_chunks])
    saved_title     = chunk_sessions[session_id]["title"]
    saved_subject   = chunk_sessions[session_id]["subject"]

    print(f"[CHUNK] Full ({len(sorted_chunks)} chunks): {full_transcript[:150]}...")
    del chunk_sessions[session_id]

    try:
        corrected, summary = correct_and_summarize(full_transcript)
        lecture = save_to_db(saved_title, saved_subject,
                             corrected, summary, db)
        return {
            "status":     "complete",
            "lecture_id": lecture.id,
            "title":      lecture.title,
            "subject":    lecture.subject,
            "transcript": lecture.transcript,
            "summary":    lecture.summary,
            "created_at": lecture.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "message":    "Lecture saved!"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Finalization error: {str(e)}")

# ── Route 4 : Debug audio ──────────────────────────────────────
@app.post("/debug_audio/", tags=["Debug"])
async def debug_audio(
    file:            UploadFile = File(...),
    sample_rate:     int        = Form(default=16000),
    channels:        int        = Form(default=1),
    bits_per_sample: int        = Form(default=16),
    language:        str        = Form(default="ta"),
    initial_prompt:  str        = Form(default=""),
):
    pcm_data  = await file.read()
    wav_bytes = build_wav_header(
        len(pcm_data), sample_rate, channels, bits_per_sample
    ) + pcm_data

    temp_path = os.path.join(TEMP_DIR, f"debug_{uuid.uuid4()}.wav")
    try:
        with open(temp_path, "wb") as f:
            f.write(wav_bytes)

        samples  = struct.unpack(f"<{len(pcm_data)//2}h", pcm_data)
        max_amp  = max(abs(s) for s in samples)
        avg_amp  = sum(abs(s) for s in samples) // len(samples)
        duration = len(pcm_data) / (sample_rate * channels * (bits_per_sample // 8))

        transcript = transcribe_audio(temp_path, language, initial_prompt)

        quality = (
            "✅ GOOD"     if max_amp > 5000 else
            "⚠️ LOW"      if max_amp > 500  else
            "❌ TOO LOW — wrong bit shift"
        )

        return {
            "duration_s":    round(duration, 2),
            "max_amplitude": max_amp,
            "avg_amplitude": avg_amp,
            "audio_quality": quality,
            "transcript":    transcript,
            "prompt_used":   initial_prompt,
            "hint": (
                "If max_amplitude < 500, change >> 14 to >> 11 in ESP32. "
                "If 500–5000, increase GAIN_FACTOR. If > 5000, audio is good."
            )
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# ── Route 5 : Get all lectures ─────────────────────────────────
@app.get("/lectures/", response_model=List[LectureResponse], tags=["Lectures"])
def get_lectures(db: Session = Depends(get_db)):
    return [
        LectureResponse.from_orm(l)
        for l in db.query(Lecture).order_by(Lecture.id.desc()).all()
    ]

# ── Route 6 : Get single lecture ───────────────────────────────
@app.get("/lectures/{lecture_id}", response_model=LectureResponse, tags=["Lectures"])
def get_lecture(lecture_id: int, db: Session = Depends(get_db)):
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(404, "Lecture not found")
    return LectureResponse.from_orm(lecture)

# ── Route 7 : Update lecture ───────────────────────────────────
@app.patch("/lectures/{lecture_id}", response_model=LectureResponse, tags=["Lectures"])
def update_lecture(
    lecture_id: int,
    data:       LectureUpdate,
    db:         Session = Depends(get_db)
):
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(404, "Lecture not found")
    for key, value in data.dict(exclude_unset=True).items():
        setattr(lecture, key, value)
    db.commit()
    db.refresh(lecture)
    return LectureResponse.from_orm(lecture)

# ── Route 8 : Delete lecture ───────────────────────────────────
@app.delete("/lectures/{lecture_id}", tags=["Lectures"])
def delete_lecture(lecture_id: int, db: Session = Depends(get_db)):
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(404, "Lecture not found")
    db.delete(lecture)
    db.commit()
    return {"message": f"Lecture {lecture_id} deleted successfully"}

# ════════════════════════════════════════════════════════════
#  SERVE FRONTEND  — must be LAST, after all API routes
# ════════════════════════════════════════════════════════════
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/app", StaticFiles(directory=frontend_path, html=True), name="frontend")