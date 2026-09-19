from pathlib import Path
from pypdf import PdfReader
from docx import Document


def extract_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)

    text = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text.append(page_text)

    return "\n".join(text).strip()


def extract_from_docx(file_path: str) -> str:
    document = Document(file_path)

    return "\n".join(
        paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()
    ).strip()


def extract_resume_text(file_path: str) -> str:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    extension = path.suffix.lower()

    if extension == ".pdf":
        return extract_from_pdf(file_path)

    if extension == ".docx":
        return extract_from_docx(file_path)

    raise ValueError("Unsupported file type. Use PDF or DOCX.")
