# Smart Classroom — Live Lecture to Auto Notes

## Overview

Smart Classroom is an AI-powered lecture transcription and note generation system designed for real classroom use. The system captures spoken lecture audio either from a **browser microphone** or from an **ESP32 IoT hardware device** installed in the classroom, and then automatically processes the audio through a three-stage AI pipeline — speech-to-text transcription, grammar correction, and summarization — before storing the final structured notes in a MySQL database.

Students can access, view, edit, and delete all saved lecture notes at any time from any device through the web frontend dashboard.

The project solves a real problem faced by students: missing important content during lectures, struggling to take notes while listening, and not having a reliable way to review what was taught. This system removes all of that friction entirely — every word spoken in class is captured, cleaned, and saved automatically.

---

## Table of Contents

1. [Project Goals](#project-goals)
2. [System Architecture](#system-architecture)
3. [AI Pipeline Explained](#ai-pipeline-explained)
4. [Technology Stack](#technology-stack)
5. [Project Structure](#project-structure)
6. [File-by-File Description](#file-by-file-description)
7. [Database Design](#database-design)
8. [API Reference](#api-reference)
9. [Backend Setup](#backend-setup)
10. [Frontend Setup](#frontend-setup)
11. [ESP32 Hardware Setup](#esp32-hardware-setup)
12. [How the Chunked Upload Works](#how-the-chunked-upload-works)
13. [CORS and Multi-Origin Support](#cors-and-multi-origin-support)
14. [Dependencies](#dependencies)
15. [Project Status](#project-status)
16. [Future Improvements](#future-improvements)
17. [Author](#author)

---

## Project Goals

- Automatically convert spoken classroom lectures into clean written notes without any manual effort from students.
- Support two audio input modes: browser-based recording for manual uploads and ESP32-based IoT capture for fully automatic, device-free classroom recording.
- Apply a complete NLP post-processing pipeline (grammar correction + summarization) on top of raw transcriptions to produce clean, readable notes.
- Store all lectures in a MySQL database so students can retrieve them at any time.
- Provide a clean web interface where students can manage all their saved lecture notes.

---

## System Architecture

The system has three major layers that work together:

```
AUDIO INPUT LAYER
├── Browser (MediaRecorder API → WAV file → /uploadfile/)
└── ESP32 IoT Device (PCM chunks over Wi-Fi → /uploadchunk/)
        │
        ▼
FASTAPI BACKEND (main.py) — API version 0.6.0
├── Step 1: Receive audio (WAV or raw PCM)
├── Step 2: Build WAV header if raw PCM (for ESP32 input)
├── Step 3: Transcribe audio using OpenAI Whisper (small model)
│           └── Task: "translate" (transcribes and translates to English)
│           └── Default language: Tamil ("ta")
│           └── Supports optional initial_prompt for domain context
├── Step 4: Grammar correction using prithivida/grammar_error_correcter_v1
│           └── Input prefix: "gec: <raw_transcript>"
│           └── max_length: 512 tokens
└── Step 5: Summarization using facebook/bart-large-cnn
            └── max_length: 150 tokens, min_length: 40 tokens
                    │
                    ▼
DATABASE LAYER
└── MySQL via SQLAlchemy ORM
    └── Table: lectures (id, subject, title, transcript, summary, created_at)
                    │
                    ▼
FRONTEND LAYER (HTML / CSS / JavaScript)
├── index.html          — Main dashboard (list all lectures)
├── Upload.html         — Record or upload audio, submit with title + subject
├── lectures.html       — Browse all lectures
└── Lecturedetail.html  — View full transcript and summary of one lecture
```

---

## AI Pipeline Explained

Every audio file received by the backend goes through three sequential AI stages:

### Stage 1 — Speech-to-Text (OpenAI Whisper)

The Whisper `small` model is loaded at server startup. When audio arrives, the `transcribe_audio()` function is called with the file path, language code, and an optional initial prompt. The model is run in `translate` task mode, meaning it transcribes audio in any language (default: Tamil) and translates it to English in one step. The `fp16=False` flag is set for CPU compatibility. The raw transcript text is returned as a string.

```python
result = whisper_model.transcribe(
    path,
    task="translate",
    language=language,       # default: "ta" (Tamil)
    fp16=False,
    verbose=False,
    initial_prompt=initial_prompt if initial_prompt.strip() else None
)
```

### Stage 2 — Grammar Correction (Hugging Face Transformers / T5)

The raw Whisper output often contains run-on sentences, missing punctuation, and grammatical errors because it is a direct speech transcript. The `grammar_pipe` loaded from `prithivida/grammar_error_correcter_v1` processes the raw text with the `gec:` prefix to produce a grammatically corrected version.

```python
corrected = grammar_pipe(
    f"gec: {raw_text}",
    max_length=512,
    truncation=True
)[0]["generated_text"]
```

### Stage 3 — Summarization (BART Large CNN)

After grammar correction, the full corrected transcript is passed to the `facebook/bart-large-cnn` summarization pipeline. This produces a short, high-quality summary of the entire lecture that students can read at a glance.

```python
summary = summarizer(
    corrected,
    max_length=150,
    min_length=40,
    do_sample=False
)[0]["summary_text"]
```

All three models are loaded once at server startup and kept in memory for the lifetime of the server process. Startup logs confirm each model loads successfully:

```
[STARTUP] Loading Whisper small model...
[STARTUP] Loading grammar corrector...
[STARTUP] Loading summarizer...
[STARTUP] ✅ All models loaded!
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend framework | Python, FastAPI | REST API server |
| ASGI server | Uvicorn | Runs the FastAPI application |
| AI - Speech Recognition | OpenAI Whisper (small model) | Speech-to-text + translation to English |
| AI - Grammar Correction | Hugging Face Transformers, prithivida/grammar_error_correcter_v1 | Post-processing raw transcripts |
| AI - Summarization | facebook/bart-large-cnn | Lecture summarization |
| ORM | SQLAlchemy | Database abstraction layer |
| Database | MySQL | Persistent storage of lecture notes |
| MySQL driver | PyMySQL | Python-to-MySQL connector |
| Data validation | Pydantic | Request and response schema validation |
| Frontend | HTML5, CSS3, JavaScript ES6+ | Web interface for students |
| API communication | Fetch API | Frontend-to-backend HTTP calls |
| Hardware / IoT | ESP32 microcontroller | Wireless classroom audio capture device |
| Audio streaming | I2S microphone, raw PCM over Wi-Fi | Hardware-level audio input |

---

## Project Structure

```
smart_class-to-auto-notes/
│
├── main.py                   # Core FastAPI app — all routes, AI pipeline, and helpers
├── database_model.py         # SQLAlchemy engine, session factory, and Base
├── table.py                  # SQLAlchemy ORM model for the lectures table
├── requirements.txt          # All Python package dependencies
│
├── index.html                # Main student dashboard — lists all saved lectures
├── index.css                 # Styles for the dashboard page
├── index.js                  # JS for dashboard — fetch and render all lectures
│
├── Upload.html               # Audio upload and browser recording page
├── upload.css                # Styles for the upload page
├── upload.js                 # JS for recording via MediaRecorder API and file upload
│
├── lectures.html             # Lectures browse/listing page
├── Lecturedetail.html        # Single lecture detail — transcript, summary, edit, delete
│
├── Api.js                    # Centralized backend base URL config for all JS files
├── Style.css                 # Shared/global CSS styles across all pages
│
├── __pycache__/              # Python bytecode cache (auto-generated)
└── .gitignore                # Git ignore rules
```

---

## File-by-File Description

### `main.py`

The heart of the entire backend. 434 lines. Contains everything the server does:

- FastAPI app initialization and CORS middleware configuration (allow all origins)
- Database table auto-creation on startup via `Base.metadata.create_all`
- Loading all three AI models at startup (Whisper, grammar corrector, BART summarizer)
- `chunk_sessions` — an in-memory `defaultdict` that tracks active ESP32 chunked upload sessions
- `TEMP_DIR = "temp"` — a temporary folder for storing audio files during processing (files are deleted after processing)

Helper functions defined in `main.py`:

- `build_wav_header(pcm_size, sample_rate, channels, bits_per_sample)` — builds a valid WAV file header from raw PCM parameters using Python's `struct.pack`. This is used to wrap raw PCM data from the ESP32 into a proper WAV file so Whisper can read it.
- `transcribe_audio(path, language, initial_prompt)` — calls `whisper_model.transcribe()` with translate task and returns the text string.
- `correct_and_summarize(raw_text)` — runs grammar correction then summarization and returns both corrected text and summary.
- `save_to_db(title, subject, transcript, summary, db)` — creates a `Lecture` ORM object, commits to MySQL, and returns the saved object.
- `process_audio_file(temp_path, title, subject, language, initial_prompt, db)` — orchestrates the full pipeline: transcribe → correct → summarize → save → return response.

API route handlers:
- `GET /` — health check
- `POST /uploadfile/` — browser WAV upload
- `POST /uploadraw/` — ESP32 single-shot PCM upload
- `POST /uploadchunk/` — ESP32 chunked PCM upload with session management
- `POST /debug_audio/` — diagnostic amplitude + transcription check
- `GET /lectures/` — list all lectures
- `GET /lectures/{id}` — single lecture
- `PATCH /lectures/{id}` — partial update
- `DELETE /lectures/{id}` — delete

Pydantic schemas:
- `LectureUpdate` — optional fields for PATCH body (subject, title, transcript, summary)
- `LectureResponse` — response model with id, subject, title, transcript, summary, created_at (formatted as string)

---

### `database_model.py`

8 lines. Defines the database connection. Uses PyMySQL as the MySQL driver via SQLAlchemy's `create_engine`. Exports:
- `engine` — the database engine
- `SessionLocal` — session factory (autocommit=False, autoflush=False)
- `Base` — declarative base used by `table.py` to define ORM models

The connection URL format used:
```
mysql+pymysql://username:password@localhost:3306/smartclassroom
```

You must update this with your own MySQL credentials before running the server.

---

### `table.py`

Defines the `Lecture` SQLAlchemy ORM model. It maps to the `lectures` table and defines all columns: id (primary key, auto-increment), subject, title, transcript, summary, and created_at (auto-timestamped).

---

### `requirements.txt`

11 packages:
```
fastapi
uvicorn
sqlalchemy
pymysql
whisper
openai-whisper
transformers==4.35.0
torch
huggingface-hub
python-multipart
pydantic
```

`transformers` is pinned to `4.35.0` for compatibility with both the grammar correction and summarization Hugging Face models. `python-multipart` is required by FastAPI to handle `Form` and `File` uploads.

---

### Frontend Files

**`index.html` + `index.js` + `index.css`**
The main student dashboard. On page load, `index.js` calls `GET /lectures/` and renders each saved lecture as a card showing subject, title, date, and a preview of the summary. Clicking a lecture navigates to `Lecturedetail.html`. A delete button is available per lecture card.

**`Upload.html` + `upload.js` + `upload.css`**
The audio recording and upload interface. Students fill in a subject name and lecture title, then either:
1. Click Record to start browser microphone recording (using the `MediaRecorder` API). When recording stops, the audio blob is converted to WAV and sent to `POST /uploadfile/`.
2. Or select a pre-recorded WAV file from their device and upload it.

**`lectures.html`**
A browseable list of all saved lectures, separate from the main dashboard.

**`Lecturedetail.html`**
Displays one complete lecture: full corrected transcript, AI-generated summary, subject, title, and date. Students can edit any field inline and save changes using `PATCH /lectures/{id}`, or delete the lecture with `DELETE /lectures/{id}`.

**`Api.js`**
Exports a single constant `BASE_URL` pointing to the FastAPI backend (default: `http://127.0.0.1:8000`). All other JS files import this value so the backend URL is configured in exactly one place.

**`Style.css`**
Shared CSS rules used across multiple pages (typography, button styles, layout utilities).

---

## Database Design

The system uses a single MySQL database named `smartclassroom` with one table.

**Table: `lectures`**

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT, Primary Key, Auto-increment | Unique lecture ID |
| `subject` | VARCHAR | Subject name (e.g., Physics, Maths, Chemistry) |
| `title` | VARCHAR | Descriptive title for the lecture |
| `transcript` | TEXT | Full grammar-corrected transcript |
| `summary` | TEXT | AI-generated summary (40–150 tokens) |
| `created_at` | DATETIME | Auto-set timestamp when the lecture was saved |

Tables are created automatically on first server start via `Base.metadata.create_all(bind=engine)`. No manual SQL migration scripts are needed. Lectures are retrieved in descending order of ID (most recent first) by default.

---

## API Reference

### GET /

Health check endpoint. Returns the API version and a map of all available routes.

**Response:**
```json
{
  "status": "ok",
  "message": "SmartClassroom API v0.6.0 running",
  "routes": {
    "POST /uploadfile/": "Manual WAV upload",
    "POST /uploadraw/": "ESP32 single PCM blob",
    "POST /uploadchunk/": "ESP32 chunked PCM",
    "POST /debug_audio/": "Audio amplitude check",
    "GET /lectures/": "All lectures",
    "GET /lectures/{id}": "Single lecture",
    "PATCH /lectures/{id}": "Edit lecture",
    "DELETE /lectures/{id}": "Delete lecture"
  }
}
```

---

### POST /uploadfile/

Manual WAV file upload from the browser frontend.

**Form fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `file` | File (.wav) | Yes | — | WAV audio file recorded in browser |
| `title` | string | Yes | — | Lecture title |
| `subject` | string | Yes | — | Subject name |
| `language` | string | No | `ta` | Whisper language code (e.g., ta, en, hi) |
| `initial_prompt` | string | No | `""` | Optional text hint to guide Whisper (e.g., subject vocabulary) |

Only `.wav` files are accepted. Sending any other format returns HTTP 400.

**Response:** Full `LectureResponse` JSON object with id, subject, title, transcript, summary, created_at.

---

### POST /uploadraw/

Single-shot raw PCM upload from ESP32 for short recordings. The backend prepends a WAV header using `build_wav_header()` before passing the audio to Whisper.

**Form fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `file` | File (binary) | Yes | — | Raw PCM audio bytes |
| `title` | string | Yes | — | Lecture title |
| `subject` | string | Yes | — | Subject name |
| `language` | string | No | `ta` | Whisper language code |
| `initial_prompt` | string | No | `""` | Optional Whisper context hint |
| `sample_rate` | int | No | `16000` | Audio sample rate in Hz |
| `channels` | int | No | `1` | Number of channels (1 = mono) |
| `bits_per_sample` | int | No | `16` | Bit depth |

**Response:** Full `LectureResponse` JSON object.

---

### POST /uploadchunk/

Chunked PCM upload for long lectures from the ESP32. Each chunk is transcribed individually. When the final chunk arrives (`is_last=true`), all chunk transcripts are merged, processed through the full NLP pipeline, and saved to the database.

**Form fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `file` | File (binary) | Yes | — | Raw PCM data for this chunk |
| `session_id` | string | Yes | — | Unique session ID shared across all chunks of one lecture |
| `chunk_index` | int | Yes | — | Zero-based index of this chunk (used to order transcripts) |
| `is_last` | string | Yes | — | `"true"` if this is the final chunk, `"false"` otherwise |
| `title` | string | Yes | — | Lecture title |
| `subject` | string | Yes | — | Subject name |
| `language` | string | No | `ta` | Whisper language code |
| `initial_prompt` | string | No | `""` | Optional Whisper context hint |
| `sample_rate` | int | No | `16000` | Audio sample rate in Hz |
| `channels` | int | No | `1` | Number of channels |
| `bits_per_sample` | int | No | `16` | Bit depth |

**Response for an intermediate chunk:**
```json
{
  "status": "chunk_received",
  "chunk_index": 2,
  "transcript": "...",
  "message": "Chunk 2 OK"
}
```

**Response for the final chunk (lecture fully saved):**
```json
{
  "status": "complete",
  "lecture_id": 14,
  "title": "Newton's Laws",
  "subject": "Physics",
  "transcript": "Full corrected transcript...",
  "summary": "AI-generated summary...",
  "created_at": "2025-08-15 10:32:00",
  "message": "Lecture saved!"
}
```

---

### POST /debug_audio/

Diagnostic endpoint for testing ESP32 audio quality. Calculates amplitude statistics and runs a test transcription. Does NOT save anything to the database.

**Form fields:** Same as `/uploadraw/` but without `title` and `subject`.

**Response:**
```json
{
  "duration_s": 12.5,
  "max_amplitude": 8231,
  "avg_amplitude": 1204,
  "audio_quality": "✅ GOOD",
  "transcript": "This is the test transcription...",
  "prompt_used": "",
  "hint": "If max_amplitude < 500, change >> 14 to >> 11 in ESP32. If 500-5000, increase GAIN_FACTOR."
}
```

Audio quality thresholds:
- `max_amplitude > 5000` → GOOD (✅)
- `max_amplitude 500–5000` → LOW (⚠️ — increase gain on ESP32)
- `max_amplitude < 500` → TOO LOW (❌ — wrong bit shift in firmware)

---

### GET /lectures/

Returns all saved lectures ordered by most recent first (descending by ID).

**Response:** JSON array of `LectureResponse` objects.

---

### GET /lectures/{lecture_id}

Returns one lecture by its integer ID.

**Response:** `LectureResponse` object. Returns HTTP 404 if the ID does not exist.

---

### PATCH /lectures/{lecture_id}

Partially update a lecture. Only the fields included in the request body are updated; all others remain unchanged.

**Request body (JSON) — all fields optional:**
```json
{
  "subject": "Updated Subject",
  "title": "Updated Title",
  "transcript": "Corrected or expanded transcript text",
  "summary": "Updated summary"
}
```

**Response:** Updated `LectureResponse` object. Returns HTTP 404 if the ID does not exist.

---

### DELETE /lectures/{lecture_id}

Permanently removes a lecture from the database.

**Response:**
```json
{
  "message": "Lecture 5 deleted successfully"
}
```

Returns HTTP 404 if the ID does not exist.

---

## Backend Setup

### Prerequisites

- Python 3.10 or higher
- MySQL Server running locally or on a remote host
- `ffmpeg` installed and accessible in your system PATH (required by Whisper for audio decoding)
- At least 2–3 GB of free RAM to load Whisper + two Hugging Face transformer models
- At least 3–4 GB of free disk space for model downloads on first run

### Step-by-step Installation

```bash
# 1. Clone the repository
git clone https://github.com/mDeepaksai/smart_class-to-auto-notes.git
cd smart_class-to-auto-notes

# 2. Create a Python virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS or Linux
source venv/bin/activate

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Create the MySQL database
# Log in to MySQL and run:
# CREATE DATABASE smartclassroom;

# 5. Update the database connection string in database_model.py
# Find this line and replace with your MySQL credentials:
# db_url = "mysql+pymysql://YOUR_USERNAME:YOUR_PASSWORD@localhost:3306/smartclassroom"

# 6. Start the FastAPI server
python -m uvicorn main:app --reload
```

The server starts at `http://127.0.0.1:8000`. On first run it downloads the Whisper small model (~244 MB) and two Hugging Face models to your local cache. This can take several minutes depending on your internet speed.

Interactive Swagger API documentation is available at:
```
http://127.0.0.1:8000/docs
```

---

## Frontend Setup

No build tools, Node.js, or frameworks are required. The entire frontend is plain HTML, CSS, and JavaScript.

### Running locally

Serve the files using Python's built-in HTTP server:

```bash
# From the project root directory
python -m http.server 3000
```

Then open `http://localhost:3000/index.html` in your browser.

Alternatively, you can open the HTML files directly in your browser (double-click `index.html`). Since the backend has CORS open to all origins, direct file-open access works fine in development.

### Configuring the backend URL

Open `Api.js` and verify or update the base URL:

```javascript
const BASE_URL = "http://127.0.0.1:8000";
```

If the backend is running on a different machine (for example, if ESP32 and the browser are on the same Wi-Fi network and the backend is on a laptop), change this to the laptop's local IP address, e.g., `http://192.168.1.10:8000`. This single change is all that is needed since every other JS file imports from `Api.js`.

### Using the frontend

1. Open `index.html` — the main dashboard showing all saved lectures.
2. Open `Upload.html` — to record a new lecture from the browser or upload a WAV file. Fill in the Subject and Title fields, then either click Record or choose a file.
3. Click any lecture card on the dashboard to open `Lecturedetail.html` and view the full transcript and summary.
4. From the detail page, edit any field and save, or delete the lecture.

---

## ESP32 Hardware Setup

The ESP32 hardware mode enables fully automatic classroom recording with zero student involvement. The device is placed in the classroom, captures all audio through an I2S microphone, and streams raw PCM data to the backend over Wi-Fi throughout the entire lecture.

### Hardware Components

- ESP32 development board (ESP32-WROOM-32 or compatible)
- I2S MEMS microphone module (INMP441 or SPH0645LM4H recommended)
- MicroSD card module (SPI interface) for local audio backup
- MicroSD card (any capacity)
- USB power supply or battery pack

### Wiring

Wire the INMP441 microphone to the ESP32 I2S pins:
- VDD → 3.3V
- GND → GND
- L/R → GND (for left channel / mono)
- BCLK → GPIO 26 (or as configured in firmware)
- WS (LRCLK) → GPIO 25
- SD (DOUT) → GPIO 33

Wire the SD card module to the ESP32 SPI pins:
- CS → GPIO 5
- MOSI → GPIO 23
- CLK → GPIO 18
- MISO → GPIO 19

### Firmware Configuration

1. Open the firmware in Arduino IDE or PlatformIO.
2. Set your Wi-Fi credentials:
   ```cpp
   const char* WIFI_SSID = "YourNetworkName";
   const char* WIFI_PASSWORD = "YourPassword";
   ```
3. Set the backend server address (use your laptop's local IP if on the same network):
   ```cpp
   const char* SERVER_URL = "http://192.168.1.10:8000";
   ```
4. Set default lecture info (can be updated over serial):
   ```cpp
   const char* LECTURE_TITLE = "Today's Lecture";
   const char* LECTURE_SUBJECT = "Physics";
   ```
5. Flash the firmware to the ESP32 and power it on.

### How it Works After Flashing

1. The ESP32 connects to Wi-Fi on boot.
2. It generates a unique UUID as the `session_id` for the current recording session.
3. It starts capturing audio through the I2S microphone at 16000 Hz, 16-bit, mono.
4. Every few seconds, it sends a chunk of raw PCM bytes to `POST /uploadchunk/` with the session_id, chunk_index, and all audio parameters.
5. The SD card also saves the raw PCM locally as a backup.
6. When the lecture ends (button press or timeout), the ESP32 sends the final chunk with `is_last=true`.
7. The backend assembles all chunks, runs the full AI pipeline, and saves the complete lecture. The ESP32 receives the saved lecture ID in the response.

### Testing Audio Quality

Before a real lecture, use the `POST /debug_audio/` endpoint with a short test recording to verify the ESP32 microphone is working correctly. The response tells you exactly what to change in the firmware if the audio is too quiet.

---

## How the Chunked Upload Works

Long lectures cannot be sent as a single HTTP POST request due to ESP32 memory constraints (limited RAM) and network timeout limits. The `/uploadchunk/` endpoint handles this with a stateful session-based chunking system.

**Per-chunk flow:**

1. The ESP32 generates a unique `session_id` at the start of each recording.
2. Audio is captured continuously and split into fixed-size PCM chunks (e.g., 30 seconds each).
3. Each chunk is sent as a separate POST to `/uploadchunk/` with the same `session_id` and an incrementing `chunk_index`.
4. On the backend, each chunk is immediately wrapped in a WAV header, saved to a temp file, transcribed by Whisper, and deleted from disk.
5. The chunk transcript is stored in the in-memory `chunk_sessions` dictionary under the session's key.
6. The backend responds to the ESP32 confirming the chunk was received.

**Final chunk flow:**

7. When the ESP32 sends `is_last=true`, the backend sorts all stored transcripts by `chunk_index`.
8. All chunk transcripts are concatenated into one full lecture transcript.
9. The grammar corrector and summarizer run once on the full combined text (not per-chunk).
10. The complete corrected transcript and summary are saved to MySQL.
11. The in-memory session data is cleared.
12. The backend returns the full saved lecture details.

This design gives both efficiency (Whisper runs in parallel with recording across chunks) and quality (NLP post-processing operates on the full lecture text, not short fragments).

---

## CORS and Multi-Origin Support

The backend is configured to accept requests from any origin:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

This allows the frontend to be served from any domain, port, or opened directly as a local file from disk (`file://`) and still communicate with the FastAPI backend without browser CORS errors. It also allows the ESP32 to POST to the API from any IP address on the local network.

For production deployment, change `allow_origins=["*"]` to a specific list of trusted domains for security.

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | latest | REST API framework |
| uvicorn | latest | ASGI server to run FastAPI |
| sqlalchemy | latest | ORM for MySQL database |
| pymysql | latest | Python MySQL connection driver |
| whisper | latest | OpenAI Whisper package |
| openai-whisper | latest | Whisper model loader and inference |
| transformers | 4.35.0 (pinned) | Hugging Face pipeline for grammar correction and summarization |
| torch | latest | PyTorch — backend engine for all AI models |
| huggingface-hub | latest | Downloads and caches Hugging Face models |
| python-multipart | latest | Required by FastAPI to handle Form + File multipart requests |
| pydantic | latest | Request validation and response serialization |

Install everything at once:
```bash
pip install -r requirements.txt
```

On first run, the following models will be automatically downloaded and cached locally:
- OpenAI Whisper small (~244 MB)
- prithivida/grammar_error_correcter_v1 (~900 MB)
- facebook/bart-large-cnn (~1.6 GB)

Ensure you have internet access and enough disk space on first startup.

---

## Project Status

| Component | Status |
|-----------|--------|
| FastAPI backend with all 8 API routes | Complete |
| MySQL database integration with SQLAlchemy ORM | Complete |
| OpenAI Whisper speech-to-text transcription pipeline | Complete |
| Grammar correction using Hugging Face T5 model | Complete |
| Lecture summarization using BART Large CNN | Complete |
| WAV header builder for raw PCM data from ESP32 | Complete |
| In-memory chunked upload session management | Complete |
| Debug audio endpoint with amplitude diagnostics | Complete |
| HTML/CSS/JS frontend dashboard | Complete |
| Browser microphone recording via MediaRecorder API | Complete |
| WAV file upload from browser | Complete |
| Lecture detail view with edit and delete | Complete |
| ESP32 IoT hardware integration | Complete |
| Chunked PCM audio streaming from embedded device | Complete |
| SD card local audio backup on ESP32 | Complete |

---

## Future Improvements

- Real-time live transcription using WebSockets so students see notes appear word by word as the lecture happens, without waiting for the session to end
- Fine-tuning Whisper on Tamil academic vocabulary to improve accuracy for subject-specific technical terms
- Student login and authentication so each student has their own private note library
- Per-student lecture management with the ability to share notes with classmates
- Search and filter on the dashboard — search by subject, date range, or keyword in the transcript
- Multi-language support with automatic language detection instead of requiring a language code parameter
- Automatic subject and title detection from transcript content using NLP classification
- Integration with Learning Management Systems such as Moodle, Google Classroom, or Canvas to push notes directly into course modules
- Mobile application for Android and iOS to record lectures and read notes on phone
- Export lectures as PDF or Word document for offline study
- Noise filtering and audio enhancement preprocessing before Whisper transcription to handle noisy classroom environments

---

## Author

**Mallarpu Deepak Sai**
2nd Year ECE Student — KIT, Tamil Nadu

GitHub: https://github.com/mDeepaksai
Email: mdeepaksai806@gmail.com
LinkedIn: https://linkedin.com/in/your-link

---

## License

This project is open source and available under the MIT License.
