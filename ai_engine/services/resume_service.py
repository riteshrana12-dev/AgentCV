import re
from pathlib import Path
from typing import Optional

from langchain_core.document_loaders import Blob

from ai_engine.tools.docx_parser import InMemoryDocxParser
from ai_engine.tools.pdf_parser import extract_text_from_pdf

_docx_parser = InMemoryDocxParser()


def _extract_raw_text(file_bytes: bytes, filename: str) -> tuple[str, str]:
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_bytes), "pdf"

    if ext in (".docx", ".doc"):
    
        blob = Blob.from_data(file_bytes, metadata={"source": filename})
        documents = list(_docx_parser.lazy_parse(blob))
        text = documents[0].page_content if documents else ""
            # Normalize spacing for .docx files to avoid excessive blank lines
        if text and ext == ".docx":
            text = _normalize_docx_paragraph_spacing(text)
        return text, "docx" if ext == ".docx" else "doc"

    raise ValueError(f"Unsupported file type: {ext or '(none)'}. Use .pdf, .docx, or .doc.")

def _normalize_docx_paragraph_spacing(raw_text: str) -> str:
    
    lines = raw_text.split("\n")
    result: list[str] = []
    i = 0
    while i < len(lines):
        if lines[i].strip() == "":
            j = i
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j - i >= 2:
                result.append("")
            i = j
        else:
            result.append(lines[i])
            i += 1
    return "\n".join(result)