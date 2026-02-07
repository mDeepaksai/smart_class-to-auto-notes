from fastapi import FastAPI, UploadFile, File, HTTPException
import os
import shutil
import uuid

app = FastAPI(title="auto notes", version="0.1.0")

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)


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

        return {
            "message": "File uploaded successfully",
            "temp_file": temp_filename
        }

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
