import re
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url: str) -> str:
    """Extract a YouTube video ID from common URL formats."""
    if not url or not url.strip():
        raise ValueError("Please enter a YouTube URL.")

    parsed = urlparse(url.strip())
    host = parsed.netloc.lower().replace("www.", "")

    video_id = None
    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
    elif host.endswith("youtube.com"):
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [None])[0]
        elif parsed.path.startswith(("/shorts/", "/embed/", "/live/")):
            parts = parsed.path.strip("/").split("/")
            if len(parts) > 1:
                video_id = parts[1]

    if not video_id or not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError("That does not look like a valid YouTube video URL.")
    return video_id


def fetch_youtube_transcript(url: str) -> str:
    """Fetch available English or Hindi captions using youtube-transcript-api."""
    video_id = extract_video_id(url)

    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id, languages=["en", "hi"])
        snippets = getattr(transcript, "snippets", transcript)
        lines = []
        for item in snippets:
            if hasattr(item, "text"):
                lines.append(item.text)
            elif isinstance(item, dict) and item.get("text"):
                lines.append(item["text"])
        result = " ".join(lines).strip()
        if result:
            return result
    except Exception as modern_error:
        # Compatibility fallback for older package versions.
        try:
            old_result = YouTubeTranscriptApi.get_transcript(
                video_id, languages=["en", "hi"]
            )
            result = " ".join(
                item.get("text", "") for item in old_result
            ).strip()
            if result:
                return result
        except Exception:
            raise ValueError(
                "Could not retrieve captions for this video. It may have no "
                "available transcript, captions may be disabled, or YouTube "
                "may be restricting access. Try another video or paste its transcript."
            ) from modern_error

    raise ValueError("No usable transcript was found for this video.")
