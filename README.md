# NotePilot AI — Intelligent Lecture Summarization & Action Item Extraction

A Python + Streamlit app that turns PDFs, pasted notes, YouTube transcripts and meeting recordings into structured summaries, key points, important concepts, action items, learning roadmaps and revision questions. Reports can be exported as PDF.

## AI provider
- **Groq Chat Completions** generates structured summaries and learning content.
- **Groq Whisper** transcribes supported audio/video uploads before summarization.
- The app uses the Groq free developer tier where available. Free-tier rate limits and service availability can change; it is not unlimited.

## Requirements
- Python 3.10 or newer
- A Groq API key: https://console.groq.com/keys

## Windows + VS Code setup
Open PowerShell in the project folder:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create a `.env` file in the project root (same folder as `app.py`) with:

```env
GROQ_API_KEY=PASTE_YOUR_GROQ_API_KEY_HERE
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_AUDIO_MODEL=whisper-large-v3-turbo
```

Replace the placeholder with your own key. Never share the key or upload `.env` to GitHub. The `.gitignore` excludes `.env`.

Run the app:

```powershell
python -m streamlit run app.py
```

## Supported inputs and limitations
- PDFs: selectable text extraction using PyMuPDF. Scanned/image-only PDFs are not OCRed in this version.
- Text/notes: pasted content.
- YouTube: requires an accessible transcript/caption track; visual frames are not analyzed.
- Audio/video: Groq Whisper accepts MP3, WAV, M4A, MP4, OGG, FLAC, MPEG, MPGA and WEBM. The free-tier direct upload limit is 25 MB per file. Video is analyzed through its audio track, not its visual frames.
- AI outputs may omit or misinterpret details. Verify important decisions, deadlines and action items.
- Summary history is stored in the current Streamlit session, not a permanent database.
