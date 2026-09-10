from langchain_community.document_loaders.blob_loaders import Blob
from langchain_community.document_loaders.parsers.pdf import PyPDFParser

def extract_text_from_pdf(file_bytes: bytes) -> str:
    blob = Blob.from_data(file_bytes, mime_type="application/pdf")
    parser = PyPDFParser()
    pages = [doc.page_content or "" for doc in parser.lazy_parse(blob)]
    return "\n\n".join(pages).strip()

