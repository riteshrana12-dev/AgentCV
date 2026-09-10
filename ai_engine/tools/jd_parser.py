from langchain_core.documents import Document
from ai_engine.schemas.resume_schema import JdRequest

def job_description_text(req:JdRequest):

    doc = Document(
        page_content=req.text,
        metadata={"type":"description"}
    )

    return doc
