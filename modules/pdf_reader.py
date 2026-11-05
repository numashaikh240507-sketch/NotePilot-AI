import fitz


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract selectable text from a PDF file."""
    if not pdf_bytes:
        raise ValueError("The uploaded PDF is empty.")

    text_parts = []
    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
            if document.is_encrypted:
                raise ValueError("This PDF is password-protected. Please upload an unlocked PDF.")

            for page_number, page in enumerate(document, start=1):
                page_text = page.get_text("text")
                if page_text.strip():
                    text_parts.append(f"\n[Page {page_number}]\n{page_text}")
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Could not read this PDF: {exc}") from exc

    extracted = "\n".join(text_parts).strip()
    if not extracted:
        raise ValueError(
            "No selectable text was found. This may be a scanned/image-only PDF. "
            "For this version, please upload a text-based PDF."
        )
    return extracted
