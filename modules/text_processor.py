import re


def clean_text(text: str) -> str:
    """Normalize whitespace while preserving paragraph boundaries."""
    if not text or not text.strip():
        raise ValueError("No text was provided.")

    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]*\n[ \t]*\n+", "\n\n", text)
    return text.strip()


def prepare_text(text: str, max_characters: int = 60000):
    """Clean text and return (text, was_truncated)."""
    cleaned = clean_text(text)
    was_truncated = len(cleaned) > max_characters
    if was_truncated:
        cleaned = cleaned[:max_characters]
    return cleaned, was_truncated
