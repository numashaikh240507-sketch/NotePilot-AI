
import json
import os
import re

import streamlit as st
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

MAX_INPUT_CHARACTERS = 18000
MAX_AUDIO_BYTES = 25 * 1024 * 1024

TEXT_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b"
)

AUDIO_MODEL = os.getenv(
    "GROQ_AUDIO_MODEL",
    "whisper-large-v3-turbo"
)


def _get_secret(name, default=None):
    """Read configuration from environment or Streamlit Secrets."""
    value = os.getenv(name)

    if value:
        return value

    try:
        value = st.secrets.get(name, default)
    except Exception:
        value = default

    return value


def _get_client():
    api_key = _get_secret("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "Groq API key is missing. Add GROQ_API_KEY "
            "to your local .env file or Streamlit Cloud Secrets."
        )

    return Groq(api_key=api_key)


def _build_prompt(text, title, source_type):
    return f"""
You are NotePilot AI, an intelligent study assistant.

Analyze the supplied learning material and return a complete study report.

TITLE: {title}
SOURCE TYPE: {source_type}

MATERIAL:
{text}

Return ONLY one valid JSON object with exactly these keys:

{{
  "title": "A suitable title",
  "summary": "A clear and detailed paragraph",
  "key_points": [
    "At least 4 key points"
  ],
  "important_concepts": [
    {{
      "term": "Concept name",
      "explanation": "Clear explanation"
    }}
  ],
  "action_items": [
    {{
      "task": "Specific task",
      "priority": "High, Medium or Low",
      "deadline": "Not specified",
      "basis": "Mention whether this is explicitly stated or a suggested next step"
    }}
  ],
  "roadmap": [
    {{
      "step": 1,
      "title": "Learning step",
      "description": "What to study",
      "estimated_time": "30 minutes"
    }}
  ],
  "study_questions": [
    "At least 5 questions"
  ]
}}

STRICT RULES:
- Generate at least 4 key points.
- Generate at least 3 important concepts.
- Generate at least 3 action items.
- Generate at least 3 roadmap steps.
- Generate at least 5 study questions.
- Every important concept MUST contain term and explanation.
- Every action item MUST contain task, priority, deadline and basis.
- Every roadmap step MUST contain step, title, description and estimated_time.
- Never leave a field empty.
- Do not invent deadlines.
- Use "Not specified" when no deadline is provided.
- Suggested activities must be labelled "Suggested next step".
- Use simple, accurate language.
- Do not add Markdown or code fences.
- Ensure the JSON is syntactically valid.
- Use double quotes for all JSON keys and string values.
- Do not include trailing commas.
- Return no text outside the JSON object.
"""


def _extract_json(response):
    response = response.strip()

    response = re.sub(
        r"^```(?:json)?\s*",
        "",
        response,
        flags=re.IGNORECASE
    )

    response = re.sub(r"\s*```$", "", response)

    start = response.find("{")
    end = response.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            "The AI did not return a valid JSON object."
        )

    return response[start:end + 1]


def _safe_list(value):
    return value if isinstance(value, list) else []


def _normalise_response(data, title):
    if not isinstance(data, dict):
        raise ValueError(
            "The AI response has an invalid structure."
        )

    aliases = {
        "key_points": ["keypoints", "key_takeaways"],
        "important_concepts": [
            "concepts",
            "important_topics"
        ],
        "action_items": [
            "next_action_items",
            "tasks"
        ],
        "roadmap": [
            "learning_roadmap",
            "study_roadmap"
        ],
        "study_questions": [
            "revision_questions",
            "questions"
        ]
    }

    for expected, alternatives in aliases.items():
        if expected not in data:
            for alternative in alternatives:
                if alternative in data:
                    data[expected] = data[alternative]
                    break

    result = {
        "title": str(data.get("title") or title),
        "summary": str(
            data.get("summary")
            or "Summary could not be generated."
        ),
        "key_points": [],
        "important_concepts": [],
        "action_items": [],
        "roadmap": [],
        "study_questions": []
    }

    # Key points
    for item in _safe_list(data.get("key_points")):
        if isinstance(item, str) and item.strip():
            result["key_points"].append(item.strip())

        elif isinstance(item, dict):
            point = (
                item.get("point")
                or item.get("text")
                or item.get("title")
            )

            if point:
                result["key_points"].append(str(point))

    # Important concepts
    for item in _safe_list(
        data.get("important_concepts")
    ):
        if not isinstance(item, dict):
            continue

        term = (
            item.get("term")
            or item.get("concept")
            or item.get("name")
        )

        explanation = (
            item.get("explanation")
            or item.get("exlication")
            or item.get("description")
            or item.get("meaning")
        )

        if term and explanation:
            result["important_concepts"].append({
                "term": str(term),
                "explanation": str(explanation)
            })

    # Action items
    for item in _safe_list(data.get("action_items")):

        if isinstance(item, str) and item.strip():
            result["action_items"].append({
                "task": item.strip(),
                "priority": "Medium",
                "deadline": "Not specified",
                "basis": "Suggested next step"
            })
            continue

        if not isinstance(item, dict):
            continue

        task = (
            item.get("task")
            or item.get("action")
            or item.get("title")
        )

        if not task or not str(task).strip():
            continue

        result["action_items"].append({
            "task": str(task),
            "priority": str(
                item.get("priority") or "Medium"
            ),
            "deadline": str(
                item.get("deadline") or "Not specified"
            ),
            "basis": str(
                item.get("basis") or "Suggested next step"
            )
        })

    # Learning roadmap
    for index, item in enumerate(
        _safe_list(data.get("roadmap")),
        start=1
    ):

        if isinstance(item, str) and item.strip():
            result["roadmap"].append({
                "step": index,
                "title": item,
                "description": item,
                "estimated_time": "Not specified"
            })
            continue

        if not isinstance(item, dict):
            continue

        step_title = (
            item.get("title")
            or item.get("topic")
            or item.get("name")
        )

        if not step_title:
            continue

        result["roadmap"].append({
            "step": item.get("step") or index,
            "title": str(step_title),
            "description": str(
                item.get("description") or step_title
            ),
            "estimated_time": str(
                item.get("estimated_time")
                or item.get("time")
                or "Not specified"
            )
        })

    # Study questions
    for item in _safe_list(
        data.get("study_questions")
    ):

        if isinstance(item, str) and item.strip():
            result["study_questions"].append(
                item.strip()
            )

        elif isinstance(item, dict):
            question = (
                item.get("question")
                or item.get("text")
            )

            if question:
                result["study_questions"].append(
                    str(question)
                )

    return result


def _generate(text, title, source_type):
    client = _get_client()
    prompt = _build_prompt(text, title, source_type)

    try:
        response = client.chat.completions.create(
            model=_get_secret(
                "GROQ_MODEL",
                "openai/gpt-oss-20b"
            ),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are NotePilot AI. Return a complete, "
                        "valid JSON object only. Never leave required "
                        "fields incomplete."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_completion_tokens=6000
        )

        raw_response = response.choices[0].message.content

        if not raw_response:
            raise ValueError(
                "Groq returned an empty response."
            )

        json_text = _extract_json(raw_response)
        parsed = json.loads(json_text)

        return _normalise_response(parsed, title)

    except json.JSONDecodeError as error:
        raise ValueError(
            "The AI returned incomplete or invalid JSON. "
            "Please try again."
        ) from error

    finally:
        client.close()


def generate_summary(
    text,
    title="Study Material",
    source_type="Text"
):
    if not text or not text.strip():
        raise ValueError(
            "No text was provided for analysis."
        )

    cleaned_text = text.strip()[:MAX_INPUT_CHARACTERS]

    return _generate(
        cleaned_text,
        title,
        source_type
    )


def generate_media_summary(
    file_path,
    title="Meeting Recording"
):
    if not os.path.exists(file_path):
        raise ValueError(
            "The uploaded media file could not be found."
        )

    file_size = os.path.getsize(file_path)

    if file_size > MAX_AUDIO_BYTES:
        raise ValueError(
            "Audio/video file exceeds the 25 MB limit."
        )

    client = _get_client()

    try:
        with open(file_path, "rb") as media_file:
            transcription = client.audio.transcriptions.create(
                file=(
                    os.path.basename(file_path),
                    media_file.read()
                ),
                model=_get_secret(
                    "GROQ_AUDIO_MODEL",
                    "whisper-large-v3-turbo"
                ),
                response_format="text"
            )

        transcript = (
            transcription
            if isinstance(transcription, str)
            else getattr(transcription, "text", "")
        )

        if not transcript or not transcript.strip():
            raise ValueError(
                "No speech could be detected in the uploaded file."
            )

    finally:
        client.close()

    return generate_summary(
        transcript,
        title=title,
        source_type="Audio/Video Transcript"
    )
