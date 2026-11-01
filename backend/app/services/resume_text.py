"""Extract plain text from PDF or DOCX resume bytes."""

from io import BytesIO


def extract_resume_text(content: bytes, ext: str) -> str:
    ext_lower = ext.lower()
    if ext_lower == "pdf":
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(content))
        parts: list[str] = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                parts.append(t)
        return "\n".join(parts)

    if ext_lower == "docx":
        import docx

        doc = docx.Document(BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs if p.text)

    raise ValueError(f"Unsupported resume type: {ext}")
