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


