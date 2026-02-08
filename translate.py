import whisper
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

audio_path = r"C:\Users\mdeep\Downloads\voiceaudio\parrin .mp3"

print("Audio path:", audio_path)
print("Exists:", os.path.exists(audio_path))

if not os.path.exists(audio_path):
    raise FileNotFoundError("Audio file not found")

model = whisper.load_model("turbo")
result = model.transcribe(audio_path)
print(result["text"])
