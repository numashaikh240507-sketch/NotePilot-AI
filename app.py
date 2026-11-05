
import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from modules.pdf_reader import extract_pdf_text
from modules.text_processor import prepare_text
from modules.youtube_reader import fetch_youtube_transcript
from modules.ai_summarizer import generate_summary, generate_media_summary
from modules.action_extractor import get_action_items
from modules.roadmap_generator import get_roadmap_steps
from modules.pdf_exporter import create_summary_pdf

load_dotenv()

st.set_page_config(
    page_title="NotePilot AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- SESSION STATE --------------------

defaults = {
    "page": "Dashboard",
    "history": [],
    "latest_result": None,
    "latest_source": "",
    "latest_type": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def navigate(page):
    st.session_state.page = page


# -------------------- PINK & WHITE STYLING --------------------

st.markdown("""
<style>

/* Main application background */
.stApp,
[data-testid="stAppViewContainer"] {
    background: #FFF8FC !important;
    color: #B83275 !important;
}

/* General text */
.stApp p,
.stApp li,
.stApp label,
.stApp span,
.stApp [data-testid="stMarkdownContainer"],
.stApp [data-testid="stCaptionContainer"] {
    color: #B83275;
}

/* Headings */
.stApp h1,
.stApp h2,
.stApp h3,
.stApp h4,
.stApp h5,
.stApp h6 {
    color: #C02678 !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #FCEAF4 !important;
    border-right: 1px solid #F3C6DD;
}

[data-testid="stSidebar"] * {
    color: #A83275 !important;
}

/* Main title */
.main-title {
    color: #C02678 !important;
    font-size: 36px;
    font-weight: 800;
    margin-bottom: 2px;
}

/* Subtitle */
.subtitle {
    color: #B34A83 !important;
    font-size: 15px;
    margin-bottom: 22px;
}

/* Section headings */
.section-title {
    color: #C02678 !important;
    font-size: 22px;
    font-weight: 700;
}

/* Dashboard cards */
.info-card {
    background: #FFFFFF !important;
    color: #B83275 !important;
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #F2C6DE;
    min-height: 118px;
}

.info-card h3 {
    color: #C02678 !important;
}

.info-card p {
    color: #B33A7A !important;
}

.info-number {
    color: #D63384 !important;
    font-size: 29px;
    font-weight: 800;
}

.info-label {
    color: #B33A7A !important;
    font-size: 14px;
}

/* Result cards */
.result-card {
    background: #FFFFFF !important;
    border: 1px solid #F2C6DE;
    border-radius: 13px;
    padding: 18px;
    margin-bottom: 12px;
}

/* Streamlit bordered containers */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF;
    border-radius: 13px;
    border-color: #F2C6DE !important;
}

/* Input labels */
.stTextInput label,
.stTextArea label,
.stFileUploader label,
.stSelectbox label,
.stDateInput label,
.stTimeInput label {
    color: #B83275 !important;
    font-weight: 600 !important;
}

/* Input fields */
.stTextInput input,
.stTextArea textarea,
[data-baseweb="input"] input {
    color: #A83275 !important;
    background: #FFFFFF !important;
    -webkit-text-fill-color: #A83275 !important;
}

/* Input placeholders */
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #D18AAE !important;
    opacity: 1 !important;
}

/* Captions */
.stCaption,
[data-testid="stCaptionContainer"] {
    color: #B34A83 !important;
}

/* Tabs */
button[data-baseweb="tab"] {
    color: #B83275 !important;
}

/* Expanders */
[data-testid="stExpander"] {
    background: #FFFFFF !important;
    border: 1px solid #F2C6DE !important;
    border-radius: 10px;
}

[data-testid="stExpander"] summary {
    color: #C02678 !important;
}

/* Alerts */
[data-testid="stAlert"] {
    background: #FFF0F7;
    border-color: #F2C6DE;
}

[data-testid="stAlert"] p {
    color: #A83275 !important;
}

/* Buttons */
div.stButton > button {
    background: #D63384 !important;
    color: #FFFFFF !important;
    border: 0;
    border-radius: 9px;
    font-weight: 600;
}

div.stButton > button p,
div.stButton > button span {
    color: #FFFFFF !important;
}

div.stButton > button:hover {
    background: #B8246D !important;
    color: #FFFFFF !important;
}

/* Download button */
div.stDownloadButton > button {
    background: #D63384 !important;
    color: #FFFFFF !important;
    border: 0;
    border-radius: 9px;
}

div.stDownloadButton > button p {
    color: #FFFFFF !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: #FFFFFF;
    border: 1px dashed #E9A9C9;
    border-radius: 12px;
    padding: 10px;
}

/* Footer */
.footer {
    text-align: center;
    color: #C02678 !important;
    font-size: 12px;
    padding: 22px;
}

</style>
""", unsafe_allow_html=True)


# -------------------- HELPERS --------------------

def save_result(result, source_name, source_type):
    record = {
        "result": result,
        "source_name": source_name,
        "source_type": source_type,
        "created_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
    }

    st.session_state.latest_result = result
    st.session_state.latest_source = source_name
    st.session_state.latest_type = source_type

    st.session_state.history.insert(0, record)
    st.session_state.page = "Results"


def run_text_analysis(text, title, source_type, source_name):
    cleaned, truncated = prepare_text(text)

    if len(cleaned) < 40:
        st.warning(
            "There is not enough readable content to summarize. "
            "Please provide more content."
        )
        return

    if truncated:
        st.warning(
            "This source is very long. The first 60,000 characters "
            "will be analyzed in this version."
        )

    with st.spinner("NotePilot AI is analyzing your content with Groq..."):
        result = generate_summary(cleaned, title, source_type)

    save_result(result, source_name, source_type)

    st.success("Your summary has been generated!")
    st.rerun()


def render_list(items, empty_message="No items were generated."):
    if not items:
        st.info(empty_message)
        return

    for item in items:
        st.markdown(f"- {item}")


def render_results(result, source_name):

    st.markdown(
        f'<div class="main-title">{result.get("title", "Your Summary")}</div>',
        unsafe_allow_html=True
    )

    st.caption(f"Source: {source_name}")

    st.markdown("### 📖 Summary Paragraph")
    st.markdown(result.get("summary", "No summary generated."))

    st.markdown("---")

    st.markdown("### 🔑 Key Points")
    render_list(result.get("key_points", []))

    st.markdown("---")

    st.markdown("### 📚 Important Concepts")

    concepts = result.get("important_concepts", [])

    if concepts:
        for concept in concepts:
            if isinstance(concept, dict):
                with st.container(border=True):
                    st.markdown(
                        f"**{concept.get('term', 'Concept')}**"
                    )
                    st.write(concept.get("explanation", ""))
            else:
                st.write(concept)
    else:
        st.info("No important concepts were generated.")

    st.markdown("---")

    st.markdown("### ✅ Next Action Items")

    actions = get_action_items(result)

    if actions:
        for index, action in enumerate(actions):

            if isinstance(action, dict):

                task = action.get("task", "Action item")
                priority = action.get("priority", "Not specified")
                deadline = action.get("deadline", "Not specified")
                basis = action.get("basis", "")

                with st.container(border=True):

                    st.markdown(f"**{index + 1}. {task}**")

                    c1, c2 = st.columns(2)

                    c1.caption(f"Priority: {priority}")
                    c2.caption(f"Deadline: {deadline}")

                    if basis:
                        st.caption(basis)

            else:
                st.write(f"- {action}")

    else:
        st.info("No action items were generated.")

    st.markdown("---")

    st.markdown("### 🗺️ Learning Roadmap")

    roadmap = get_roadmap_steps(result)

    if roadmap:
        for index, step in enumerate(roadmap, start=1):

            if isinstance(step, dict):

                with st.expander(
                    f"Step {step.get('step', index)}: "
                    f"{step.get('title', 'Learning step')}",
                    expanded=True
                ):

                    st.write(step.get("description", ""))

                    st.caption(
                        f"Estimated time: "
                        f"{step.get('estimated_time', 'Not specified')}"
                    )

    else:
        st.info("No roadmap was generated.")

    st.markdown("---")

    st.markdown("### 🧠 Revision Questions")

    render_list(result.get("study_questions", []))

    try:

        pdf_bytes = create_summary_pdf(result, source_name)

        st.download_button(
            "📥 Download Summary as PDF",
            data=pdf_bytes,
            file_name="NotePilot_AI_Summary.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    except Exception as exc:
        st.warning(f"PDF export could not be prepared: {exc}")


# -------------------- SIDEBAR --------------------

with st.sidebar:

    st.markdown(
        "<h1 style='color:#C02678;'>📚 NotePilot AI</h1>",
        unsafe_allow_html=True
    )

    st.caption("Your Intelligent Learning Assistant")

    st.markdown("---")

    pages = [
        ("🏠 Dashboard", "Dashboard"),
        ("✨ Create Summary", "Create Summary"),
        ("📊 Results", "Results"),
        ("📂 My Summaries", "My Summaries"),
        ("ℹ️ About Project", "About Project"),
    ]

    for label, page_name in pages:

        if st.button(
            label,
            use_container_width=True,
            key=f"nav_{page_name}"
        ):
            navigate(page_name)
            st.rerun()

    st.markdown("---")

    if os.getenv("GROQ_API_KEY"):
        st.success("Groq API key detected")
    else:
        st.warning("Groq API key not configured")

    st.caption("NotePilot AI | Version 1.0")


# -------------------- DASHBOARD --------------------

if st.session_state.page == "Dashboard":

    st.markdown(
        '<div class="main-title">Welcome to NotePilot AI 👋</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Turn lectures, documents and meetings '
        'into smart summaries and actionable learning plans.</div>',
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    for col, number, label in [
        (c1, "04", "Input Methods"),
        (c2, "05", "AI Output Sections"),
        (c3, "AI", "Powered Summarization"),
    ]:

        with col:

            st.markdown(
                f'<div class="info-card">'
                f'<div class="info-number">{number}</div>'
                f'<div class="info-label">{label}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">What can NotePilot AI do?</div>',
        unsafe_allow_html=True
    )

    left, right = st.columns(2)

    with left:

        st.markdown(
            '<div class="info-card">'
            '<h3>📝 Smart Summarization</h3>'
            '<p>Convert lengthy lectures and documents into clear summaries.</p>'
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            '<div class="info-card">'
            '<h3>✅ Action Item Extraction</h3>'
            '<p>Identify tasks, deadlines and recommended next steps.</p>'
            '</div>',
            unsafe_allow_html=True
        )

    with right:

        st.markdown(
            '<div class="info-card">'
            '<h3>🔑 Key Point Extraction</h3>'
            '<p>Find important concepts, definitions and information.</p>'
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            '<div class="info-card">'
            '<h3>🗺️ Learning Roadmap</h3>'
            '<p>Generate an ordered learning path from the supplied material.</p>'
            '</div>',
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("✨ Start Creating Summary", use_container_width=True):
        navigate("Create Summary")
        st.rerun()


# -------------------- CREATE SUMMARY --------------------

elif st.session_state.page == "Create Summary":

    st.markdown(
        '<div class="main-title">Create Your Summary ✨</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Choose an input source and let NotePilot AI analyze it.</div>',
        unsafe_allow_html=True
    )

    pdf_tab, notes_tab, youtube_tab, meeting_tab = st.tabs([
        "📄 PDF Upload",
        "📝 Text / Notes",
        "▶️ YouTube Link",
        "🎙️ Meeting Upload"
    ])

    # PDF UPLOAD

    with pdf_tab:

        st.subheader("Upload a PDF document")

        pdf_file = st.file_uploader(
            "Choose PDF",
            type=["pdf"],
            key="pdf_file"
        )

        if pdf_file:

            st.success(f"Selected: {pdf_file.name}")

            if st.button("✨ Generate PDF Summary", key="analyze_pdf"):

                try:

                    pdf_text = extract_pdf_text(pdf_file.getvalue())

                    run_text_analysis(
                        pdf_text,
                        pdf_file.name,
                        "lecture/document",
                        pdf_file.name
                    )

                except Exception as exc:
                    st.error(str(exc))

    # TEXT / NOTES

    with notes_tab:

        st.subheader("Paste your notes")

        notes_title = st.text_input(
            "Lecture or meeting title",
            placeholder="Introduction to Machine Learning",
            key="notes_title"
        )

        notes_text = st.text_area(
            "Paste your notes here",
            height=240,
            placeholder="Paste class notes, lecture content or meeting notes...",
            key="notes_text"
        )

        if st.button("✨ Generate Notes Summary", key="analyze_notes"):

            try:

                if not notes_text.strip():

                    st.warning("Please paste some notes first.")

                else:

                    run_text_analysis(
                        notes_text,
                        notes_title or "Pasted Notes",
                        "notes",
                        notes_title or "Pasted Notes"
                    )

            except Exception as exc:
                st.error(str(exc))

    # YOUTUBE

    with youtube_tab:

        st.subheader("Summarize a YouTube video")

        youtube_url = st.text_input(
            "YouTube video URL",
            placeholder="https://www.youtube.com/watch?v=...",
            key="youtube_url"
        )

        st.caption(
            "The video needs accessible captions. "
            "This version summarizes the transcript, not the visual content."
        )

        if st.button("✨ Generate YouTube Summary", key="analyze_youtube"):

            try:

                with st.spinner("Fetching available captions..."):
                    transcript = fetch_youtube_transcript(youtube_url)

                run_text_analysis(
                    transcript,
                    "YouTube Lecture",
                    "YouTube transcript",
                    youtube_url
                )

            except Exception as exc:
                st.error(str(exc))

    # MEETING UPLOAD

    with meeting_tab:

        st.subheader("Upload a meeting recording")

        st.info(
            "Audio/video files are transcribed with Groq Whisper and "
            "summarized with Groq AI. Free-tier audio uploads are limited "
            "to 25 MB. Only upload recordings you have permission to share."
        )

        meeting_file = st.file_uploader(
            "Choose an audio or video recording",
            type=[
                "mp3", "wav", "m4a", "ogg", "flac",
                "mp4", "mpeg", "mpga", "webm"
            ],
            key="meeting_file",
        )

        if meeting_file:

            st.success(
                f"Selected: {meeting_file.name} "
                f"({meeting_file.size / (1024 * 1024):.1f} MB)"
            )

            if meeting_file.size > 25 * 1024 * 1024:

                st.error(
                    "Groq free-tier transcription supports audio/video "
                    "uploads up to 25 MB. Please compress the recording "
                    "or choose a shorter file."
                )

            elif st.button(
                "✨ Analyze Meeting Recording",
                key="analyze_meeting"
            ):

                try:

                    with st.spinner(
                        "Transcribing your recording and generating "
                        "the summary with Groq..."
                    ):

                        result = generate_media_summary(
                            meeting_file.getvalue(),
                            meeting_file.name,
                            meeting_file.type or "application/octet-stream",
                        )

                    save_result(
                        result,
                        meeting_file.name,
                        "Meeting recording"
                    )

                    st.success("Meeting analysis completed!")
                    st.rerun()

                except Exception as exc:
                    st.error(f"Meeting processing failed: {exc}")

        st.markdown("**Or paste a meeting transcript**")

        meeting_title = st.text_input(
            "Meeting title",
            key="meeting_title"
        )

        meeting_text = st.text_area(
            "Meeting transcript",
            height=150,
            key="meeting_text"
        )

        if st.button(
            "✨ Summarize Meeting Transcript",
            key="analyze_meeting_text"
        ):

            try:

                if not meeting_text.strip():

                    st.warning("Upload a recording or paste a transcript.")

                else:

                    run_text_analysis(
                        meeting_text,
                        meeting_title or "Meeting Transcript",
                        "meeting transcript",
                        meeting_title or "Meeting Transcript"
                    )

            except Exception as exc:
                st.error(str(exc))


# -------------------- RESULTS --------------------

elif st.session_state.page == "Results":

    st.markdown(
        '<div class="main-title">Your AI Results 📊</div>',
        unsafe_allow_html=True
    )

    result = st.session_state.latest_result

    if result:

        render_results(
            result,
            st.session_state.latest_source
        )

    else:

        st.info(
            "You haven't generated a summary yet. "
            "Choose Create Summary to begin."
        )

        if st.button("Create your first summary"):

            navigate("Create Summary")
            st.rerun()


# -------------------- HISTORY --------------------

elif st.session_state.page == "My Summaries":

    st.markdown(
        '<div class="main-title">My Summaries 📂</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Summaries generated during this app session.</div>',
        unsafe_allow_html=True
    )

    history = st.session_state.history

    if not history:

        st.info(
            "No summaries yet. Your generated summaries will appear here."
        )

    else:

        for index, item in enumerate(history):

            with st.container(border=True):

                col1, col2 = st.columns([4, 1])

                with col1:

                    st.markdown(
                        f"**{item['result'].get('title', 'Untitled Summary')}**"
                    )

                    st.caption(
                        f"{item['source_type']} • "
                        f"{item['created_at']} • "
                        f"{item['source_name']}"
                    )

                with col2:

                    if st.button("Open", key=f"history_{index}"):

                        st.session_state.latest_result = item["result"]
                        st.session_state.latest_source = item["source_name"]
                        st.session_state.latest_type = item["source_type"]

                        navigate("Results")
                        st.rerun()


# -------------------- ABOUT PROJECT --------------------

elif st.session_state.page == "About Project":

    st.markdown(
        '<div class="main-title">About NotePilot AI 📚</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">An intelligent assistant that turns long '
        'learning and meeting content into clear, useful outcomes.</div>',
        unsafe_allow_html=True
    )

    st.markdown("### Project Overview")

    st.write(
        "NotePilot AI – Intelligent Lecture Summarization & Action Item "
        "Extraction System is a Python-based application designed to help "
        "students and professionals review lectures, documents and meeting "
        "recordings more efficiently. It uses the Groq API for fast "
        "AI-powered analysis and Groq Whisper for speech-to-text "
        "transcription, then organizes the content into easy-to-read sections."
    )

    st.markdown("### Supported Input Sources")

    source_cols = st.columns(4)

    source_details = [
        ("📄 PDF Documents", "Extracts readable text from PDF files."),
        ("📝 Text & Notes", "Analyzes notes pasted directly into the app."),
        ("▶️ YouTube Videos", "Uses available video captions or transcripts."),
        ("🎙️ Meetings", "Analyzes supported audio/video recordings or transcripts."),
    ]

    for col, (heading, detail) in zip(source_cols, source_details):

        with col:

            st.markdown(
                f'<div class="info-card">'
                f'<h3>{heading}</h3>'
                f'<p>{detail}</p>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown("### What the System Generates")

    outputs = [
        ("📖 Summary Paragraph", "A concise explanation of the source content."),
        ("🔑 Key Points", "The most relevant facts and takeaways."),
        ("📚 Important Concepts", "Key terms with short explanations."),
        ("✅ Action Items", "Tasks, priorities and deadlines when identifiable."),
        ("🗺️ Learning Roadmap", "A suggested sequence for studying the topic further."),
        ("🧠 Revision Questions", "Questions to help review and test understanding."),
        ("📥 PDF Report", "A downloadable report containing the generated results."),
    ]

    for i in range(0, len(outputs), 2):

        left, right = st.columns(2)

        for col, item in zip((left, right), outputs[i:i+2]):

            with col:

                st.markdown(
                    f'<div class="info-card">'
                    f'<h3>{item[0]}</h3>'
                    f'<p>{item[1]}</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### How It Works")

    st.markdown("""
    1. **Choose an input:** upload a PDF or meeting recording, paste notes, or provide a YouTube link.
    2. **Extract the content:** the app reads document text or obtains an available transcript.
    3. **Analyze with Groq:** text is sent to the configured Groq language model; audio/video is first transcribed with Groq Whisper.
    4. **Review the results:** explore the summary, key points, concepts, action items and roadmap.
    5. **Export:** download the generated summary as a PDF report.
    """)

    st.markdown("### Technologies Used")

    tech = [
        ("Python", "Core programming language"),
        ("Streamlit", "Interactive web application interface"),
        ("Groq API", "Fast AI-powered content analysis and generation"),
        ("Groq Whisper", "Transcription of supported audio and video files"),
        ("PyMuPDF", "PDF text extraction"),
        ("YouTube Transcript API", "Retrieval of available captions/transcripts"),
        ("ReportLab", "PDF report generation"),
        ("python-dotenv", "Secure loading of environment variables"),
    ]

    for name, purpose in tech:
        st.markdown(f"- **{name}:** {purpose}")

    st.markdown("### Project Objective")

    st.write(
        "The main objective is to reduce the time and effort required to "
        "revise long lectures and meetings. NotePilot AI converts "
        "unstructured content into organized information that users can "
        "review, study and act on."
    )

    st.markdown("### Scope & Limitations")

    st.markdown("""
    - PDF extraction works best with selectable text. Scanned/image-only PDFs may need OCR, which is not included in this version.
    - YouTube summarization depends on captions or transcripts being available and accessible.
    - The YouTube feature analyzes the transcript, not the video's visual frames.
    - AI-generated summaries and action items may occasionally be incomplete or incorrect; review important details.
    - Groq free-tier audio/video transcription uploads are limited to 25 MB per file and supported file formats only.
    - Meeting recordings should only be uploaded when you have permission to share and process them.
    - Summary history is kept in the current app session and is not a permanent cloud database.
    """)

    st.markdown("### Project Information")

    st.write("**Project name:** NotePilot AI")
    st.write("**Project type:** AI-powered lecture and meeting summarization system")
    st.write("**Version:** 1.0")


# -------------------- FOOTER --------------------

st.markdown(
    '<div class="footer">Made with 💗 | NotePilot AI</div>',
    unsafe_allow_html=True
)
