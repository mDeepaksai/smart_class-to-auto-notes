<div align="center">

<!-- HEADER BANNER -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:1A237E,100:0288D1&height=200&section=header&text=Smart%20Classroom&fontSize=52&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=Live%20Lecture%20→%20Auto%20Notes%20%7C%20AI-Powered&descAlignY=60&descSize=18" width="100%"/>

<br/>

<!-- BADGES -->
![Status](https://img.shields.io/badge/Status-Live%20%26%20Deployed-brightgreen?style=for-the-badge&logo=railway)
![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi)
![AI](https://img.shields.io/badge/AI-OpenAI%20Whisper-412991?style=for-the-badge&logo=openai)
![Frontend](https://img.shields.io/badge/Frontend-HTML%2FJS%2FCSS-orange?style=for-the-badge&logo=html5)
![Hardware](https://img.shields.io/badge/Hardware-ESP32%20IoT-red?style=for-the-badge&logo=espressif)
![Database](https://img.shields.io/badge/Database-MySQL-4479A1?style=for-the-badge&logo=mysql)

<br/>

### 🎓 Automatically convert classroom lectures into structured digital notes — in real time.

**[🚀 Live App](https://mdeepaksai.github.io/smart_class-to-auto-notes/frontend/) &nbsp;|&nbsp; [⚡ Backend API](https://smartclassroom-production.up.railway.app) &nbsp;|&nbsp; [📖 API Docs](https://smartclassroom-production.up.railway.app/docs) &nbsp;|&nbsp; [👤 Portfolio](https://mdeepaksai.github.io/portfolio/)**

</div>

---

## 📌 What is Smart Classroom?

**Smart Classroom** is an AI-powered lecture transcription system that listens to live classroom audio and automatically converts it into clean, structured, grammar-corrected digital notes — accessible to students anytime, from any device.

It supports two input modes:
- 🌐 **Browser** — record or upload audio directly from any device
- 📡 **ESP32 IoT device** — wireless hardware deployed in the classroom, no phone needed

> Built as a real deployed product — not a college project or demo. Live and accessible now.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🎙️ **Real-time Transcription** | Live speech-to-text using OpenAI Whisper |
| ✍️ **Grammar Correction** | Automatically corrects raw transcript using T5 Transformer |
| 📝 **Auto Summarization** | Generates concise lecture summaries using BART Large CNN |
| 📡 **ESP32 IoT Support** | Wireless classroom device streams PCM audio chunks over Wi-Fi |
| 🌐 **Browser Recording** | Students can record or upload WAV/PCM files directly |
| 🗂️ **Lecture Dashboard** | View, edit, delete, and tag all saved lecture notes |
| 📦 **Chunked Upload** | Long lectures handled via chunk-based streaming from ESP32 |
| 🗄️ **Database Storage** | All notes stored in MySQL via SQLAlchemy ORM |
| 📱 **Responsive UI** | Works on desktop and mobile |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python, FastAPI, SQLAlchemy, MySQL, Uvicorn |
| **Frontend** | HTML5, CSS3, JavaScript ES6+, Fetch API |
| **AI / ML** | OpenAI Whisper, Hugging Face Transformers, BART-Large-CNN, T5 Grammar |
| **Hardware / IoT** | ESP32, I2S Microphone Module, SD Card, Wi-Fi PCM Streaming |
| **Deployment** | Railway (backend), GitHub Pages (frontend) |
| **Database** | MySQL with SQLAlchemy ORM (auto-table creation) |

---

## 🔁 How It Works

```
Classroom Audio (Mic / ESP32)
        │
        ▼
  FastAPI Backend
        │
        ├──▶  OpenAI Whisper   →  Raw Transcript
        │
        ├──▶  T5 Transformer   →  Grammar Corrected Text
        │
        ├──▶  BART CNN         →  Summary of Lecture
        │
        └──▶  MySQL Database   →  Saved & Retrievable Notes
                                          │
                                          ▼
                               Student Dashboard (Frontend)
                               View · Edit · Delete · Search
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/uploadfile/` | Manual WAV file upload from browser |
| `POST` | `/uploadraw/` | Raw PCM upload from ESP32 |
| `POST` | `/uploadchunk/` | Chunked PCM streaming from ESP32 |
| `POST` | `/debug_audio/` | Check audio amplitude and quality |
| `GET` | `/lectures/` | Retrieve all saved lecture notes |
| `GET` | `/lectures/{id}` | Retrieve a single lecture by ID |
| `PATCH` | `/lectures/{id}` | Edit a lecture's content |
| `DELETE` | `/lectures/{id}` | Delete a lecture |

> 📖 **Interactive API Docs:** [https://smartclassroom-production.up.railway.app/docs](https://smartclassroom-production.up.railway.app/docs)

---

## 🚀 Getting Started

### Backend Setup

```bash
# 1. Clone the repository
git clone https://github.com/mDeepaksai/smart_class-to-auto-notes.git
cd smart_class-to-auto-notes

# 2. Create & activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your MySQL database in database_model.py

# 5. Start the server
python -m uvicorn main:app --reload
```

Visit **http://127.0.0.1:8000/docs** for the interactive Swagger UI.

---

### Frontend Setup

```bash
# Navigate to the frontend folder
cd frontend

# Open index.html directly in browser
# OR serve with Live Server extension in VS Code
```

> The frontend connects to the FastAPI backend at `http://127.0.0.1:8000`.

---

### Database Setup

1. Create a MySQL database locally or on a cloud server
2. Update the connection string in `database_model.py`:
   ```python
   DATABASE_URL = "mysql+pymysql://user:password@localhost/smartclassroom"
   ```
3. Tables are **auto-created** on first server startup via SQLAlchemy

---

### ESP32 Hardware Setup

1. Flash the ESP32 with the provided firmware
2. Connect the **I2S microphone module** to the ESP32's I2S pins
3. Insert an **SD card** for local audio backup
4. Set your Wi-Fi credentials and backend URL in the firmware config
5. Power on — ESP32 will auto-capture audio and stream chunks to `/uploadchunk/`
6. Backend assembles, transcribes, corrects, summarizes, and saves notes automatically

---

## 🗂️ Project Structure

```
smart_class-to-auto-notes/
│
├── main.py                 # FastAPI app — all API routes
├── database_model.py       # SQLAlchemy models & DB connection
├── table.py                # Database table definitions
├── requirements.txt        # Python dependencies
│
├── index.html              # Landing page
├── index.css               # Landing page styles
├── index.js                # Landing page JS
│
├── Upload.html             # Audio upload page
├── upload.css              # Upload page styles
├── upload.js               # Upload page logic
│
├── lectures.html           # Lecture dashboard
├── Lecturedetail.html      # Single lecture view
├── Style.css               # Shared styles
├── Api.js                  # Frontend API calls
│
└── .gitignore
```

---

## ✅ Project Status

- [x] FastAPI backend fully implemented
- [x] MySQL database integration with SQLAlchemy ORM
- [x] OpenAI Whisper speech recognition pipeline
- [x] Grammar correction using Hugging Face T5
- [x] Lecture summarization using BART Large CNN
- [x] HTML/JS/CSS frontend completed
- [x] ESP32 hardware integration with chunked PCM streaming
- [x] Deployed live on Railway + GitHub Pages

---

## 🔮 Future Improvements

- [ ] Real-time streaming transcription (WebSocket)
- [ ] Multi-language transcription support (Tamil, Hindi, Telugu)
- [ ] Student login & per-student note management
- [ ] Search and filter lectures by subject, date, or keyword
- [ ] Integration with LMS platforms (Moodle, Google Classroom)
- [ ] Fine-tuned Whisper model for classroom-specific audio
- [ ] Mobile app (React Native)

---

## 🔗 My Other Projects

<table>
<tr>
<td align="center" width="50%">

### 🎙️ VoiceID — Free AI Voice Detector

Detect if a voice is **human or AI-generated** in seconds.

- 88 acoustic features analysed per audio file
- Supports English, Tamil, Hindi, Malayalam, Telugu
- Upload MP3/WAV or record live in browser
- Confidence score + JSON export
- 90+ visitors · 26+ analyses · Free, no login

**[🔴 Live Demo](https://mdeepaksai.github.io/human-or-AI/) &nbsp;|&nbsp; [📖 API Docs](https://human-or-ai-production-8e10.up.railway.app/docs)**

</td>
<td align="center" width="50%">

### 🎓 Smart Classroom (this repo)

Convert live lectures into auto-generated digital notes.

- Real-time transcription with OpenAI Whisper
- Grammar correction + summarization
- ESP32 IoT hardware support
- Browser recording + dashboard
- Live on Railway + GitHub Pages

**[🚀 Live App](https://mdeepaksai.github.io/smart_class-to-auto-notes/frontend/) &nbsp;|&nbsp; [⚡ Backend](https://smartclassroom-production.up.railway.app)**

</td>
</tr>
</table>

---

## 👨‍💻 Built By

<div align="center">

**Mallarpu Deepak Sai**
2nd Year ECE Student — KIT, Tamil Nadu

[![Portfolio](https://img.shields.io/badge/Portfolio-Visit-1A237E?style=for-the-badge&logo=github)](https://mdeepaksai.github.io/portfolio/)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=for-the-badge&logo=linkedin)](https://linkedin.com/in/mdeepaksai)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=for-the-badge&logo=github)](https://github.com/mDeepaksai)
[![Email](https://img.shields.io/badge/Email-Contact-D14836?style=for-the-badge&logo=gmail)](mailto:mdeepaksai806@gmail.com)

**Co-contributor:** Smriti Kumari

</div>

---

<div align="center">

⭐ **If this project helped you or impressed you, please star the repo!** ⭐

It keeps me motivated to build more open tools. 🚀

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0288D1,100:1A237E&height=100&section=footer" width="100%"/>

</div>