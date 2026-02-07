import whisper
import os

model = whisper.load_model("base")

audio_path = os.path.join("temp", "aaa.mp3")
result = model.transcribe(audio_path)

print(result["text"])
