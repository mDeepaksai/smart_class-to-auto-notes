from fastapi import FastAPI, UploadFile, File, HTTPException
import os
import shutil
import uuid
import whisper
from transformers import pipeline

app = FastAPI(title="Auto Notes API", version="0.2.0")

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


@app.get("/")
def welcome_message():
    return {
        "message": "Upload WAV file to /uploadfile/ for transcription, grammar correction, and summarization."
    }


@app.post("/uploadfile/")
async def upload_file(file: UploadFile = File(...)):

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

        return {
            "message": "File processed successfully",
            # "transcription_raw": raw_text,
            "transcription_corrected": corrected_text,
            "summary": summary_text,
            # "language_code": language_code,
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
