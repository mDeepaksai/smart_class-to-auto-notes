from fastapi import FastAPI, UploadFile, File, HTTPException,Depends
from sqlalchemy.orm import Session
import os
import shutil
import uuid
import whisper
from transformers import pipeline
from table import Lecture
import database_model

app = FastAPI(title="Auto Notes API", version="0.2.0")
database_model.Base.metadata.create_all(bind=database_model.engine)

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

whisper_model = whisper.load_model("base")

grammar_corrector = pipeline(
    task="text2text-generation",
    model="vennify/t5-base-grammar-correction"
)

summarizer = pipeline(
    task="summarization",
    model="facebook/bart-large-cnn"
)

def get_db():
    db = database_model.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def welcome_message():
    return {
        "message": "Upload WAV file to /uploadfile/ for transcription, grammar correction, and summarization."
    }

@app.get("/lectures/")
def get_lectures(db: Session = Depends(get_db)):
    lectures = db.query(Lecture).all()
    return lectures

@app.post("/uploadfile/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):

    if file.content_type != "audio/wav":
        raise HTTPException(
            status_code=400,
            detail="Only WAV files are allowed"
        )

    temp_filename = f"{uuid.uuid4()}.wav"
    temp_path = os.path.join(TEMP_DIR, temp_filename)

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = whisper_model.transcribe(temp_path, task="translate")
        raw_text = result["text"]

        corrected_output = grammar_corrector(
            f"correct grammar: {raw_text}",
            max_length=512,
            truncation=True
        )
        corrected_text = corrected_output[0]["generated_text"]

        summary_output = summarizer(
            corrected_text,
            max_length=150,
            min_length=40,
            do_sample=False
        )
        summary_text = summary_output[0]["summary_text"]

        language_map = {
            "hi": "Hindi",
            "en": "English",
            "te": "Telugu",
            "ta": "Tamil",
            "kn": "Kannada",
            "ml": "Malayalam"
        }

        language_code = result.get("language", "unknown")
        language_name = language_map.get(language_code, "Unknown")

        new_lecture = Lecture(
            subject=language_name,
            title=temp_filename,
            transcript=corrected_text,
            summary=summary_text
        )

        db.add(new_lecture)
        db.commit()
        db.refresh(new_lecture)

        return {
            "message": "File processed successfully",
            "transcription_corrected": corrected_text,
            "summary": summary_text,
            "language_name": language_name
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
