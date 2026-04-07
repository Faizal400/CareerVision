# src/core_engine/text_extraction.py

from docx import Document
from pypdf import PdfReader


def extract_cv_text(cv_file) -> str:
    name = cv_file.name.lower()

    if name.endswith(".txt"):
        return cv_file.read().decode("utf-8", errors="ignore")

    if name.endswith(".pdf"):
        reader = PdfReader(cv_file)
        return "\n".join(
            (page.extract_text() or "") for page in reader.pages
        )

    if name.endswith(".docx"):
        doc = Document(cv_file)
        return "\n".join(p.text for p in doc.paragraphs)

    return ""  # unsupported type — return empty string