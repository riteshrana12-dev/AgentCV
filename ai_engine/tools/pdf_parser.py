import re
from io import BytesIO

from langchain_community.document_loaders.blob_loaders import Blob
from langchain_community.document_loaders.parsers.pdf import PyPDFParser
from pypdf import PdfReader


def _normalize_pdf_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_with_langchain(file_bytes: bytes) -> str:
    blob = Blob.from_data(file_bytes, mime_type="application/pdf")
    parser = PyPDFParser()
    pages = [doc.page_content or "" for doc in parser.lazy_parse(blob)]
    return "\n\n".join(pages)


def _extract_with_pypdf(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    pages: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text:
            pages.append(page_text)
    return "\n\n".join(pages)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = _extract_with_langchain(file_bytes)
    if text and text.strip():
        return _normalize_pdf_text(text)

    text = _extract_with_pypdf(file_bytes)
    if text and text.strip():
        return _normalize_pdf_text(text)

    raise ValueError(
        "Unable to extract readable text from the uploaded PDF. "
        "It may be scanned/image-based, password-protected, or corrupted."
    )

