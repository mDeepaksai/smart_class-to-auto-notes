from fastapi import FastAPI, UploadFile, File, HTTPException
import os
import shutil
import uuid
import whisper

app = FastAPI(title="auto notes", version="0.1.0")

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

model = whisper.load_model("base")

@app.get("/")
def welcome_message():
    return {
        "message": "Welcome to the auto notes API. Use the /uploadfile/ endpoint to upload a WAV file for transcription and that transcription is summarised also."
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

        result = model.transcribe(temp_path, task="translate")

        language_map = {
            "hi": "Hindi",
            "en": "English",
            "te": "Telugu",
            "ta": "Tamil",
            "kn": "Kannada",
            "ml": "Malayalam"
        }

        language_code = result["language"]
        language_name = language_map.get(language_code, "Unknown")

        return {
            "message": "File uploaded and transcribed successfully",
            "transcription": result["text"],
            "language": language_code,
            "language_name": language_name
        }

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
