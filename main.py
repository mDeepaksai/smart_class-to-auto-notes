from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Optional, List
import os
import shutil
import uuid
import whisper
from transformers import pipeline
from table import Lecture
import database_model
from datetime import datetime

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

class LectureUpdate(BaseModel):
    subject: Optional[str] = None
    title: Optional[str] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None

class LectureResponse(BaseModel):
    id: int
    subject: str
    title: str
    transcript: str
    summary: str
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

@app.get("/", tags=["General"])
def welcome_message():
    return {"message": "Upload WAV file to /uploadfile/ for transcription, grammar correction, and summarization."}

@app.get("/lectures/", response_model=List[LectureResponse], tags=["Lectures"])
def get_lectures(db: Session = Depends(get_db)):
    lectures = db.query(Lecture).all()
    return [LectureResponse.from_orm(lec) for lec in lectures]

@app.post("/uploadfile/", response_model=LectureResponse, tags=["Lectures"])
async def upload_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    subject: str = Form(...),
    db: Session = Depends(get_db)
):
    if file.content_type != "audio/wav":
        raise HTTPException(status_code=400, detail="Only WAV files are allowed")

    temp_filename = f"{uuid.uuid4()}.wav"
    temp_path = os.path.join(TEMP_DIR, temp_filename)

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = whisper_model.transcribe(temp_path, task="translate")
        raw_text = result["text"]

        corrected_text = grammar_corrector(f"correct grammar: {raw_text}", max_length=512, truncation=True)[0]["generated_text"]
        summary_text = summarizer(corrected_text, max_length=150, min_length=40, do_sample=False)[0]["summary_text"]

        new_lecture = Lecture(
            title=title,
            subject=subject,
            transcript=corrected_text,
            summary=summary_text
        )

        db.add(new_lecture)
        db.commit()
        db.refresh(new_lecture)

        return LectureResponse.from_orm(new_lecture)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.patch("/lectures/{lecture_id}", response_model=LectureResponse, tags=["Lectures"])
def update_lecture(
    lecture_id: int,
    lecture_data: LectureUpdate,
    db: Session = Depends(get_db)
):
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")

    update_dict: Dict = lecture_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(lecture, key, value)

    db.commit()
    db.refresh(lecture)
    return LectureResponse.from_orm(lecture)

@app.delete("/lectures/{lecture_id}", tags=["Lectures"])
def delete_lecture(lecture_id: int, db: Session = Depends(get_db)):
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")

    db.delete(lecture)
    db.commit()
    return {"message": "Lecture deleted successfully"}