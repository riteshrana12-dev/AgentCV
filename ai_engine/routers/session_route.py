from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from ai_engine.schemas.resume_schema import JdRequest
from ai_engine.tools.jd_parser import job_description_text
from ai_engine.services.resume_service import _extract_raw_text
router = APIRouter(prefix="/interview" , tags=["interview data"])

@router.post("/create-session")
async def mock_interview_session(resume: UploadFile = File(...),
                         sessionId: str = Form(...),
                         jd: str = Form(...),
                        ):
    
    file_bytes = await resume.read()

    if not file_bytes: 
        return {"error": "Failed to fetch the resume bytes ."}

    try:
        resume_text, _file_type = _extract_raw_text(file_bytes, resume.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    parse_jd = job_description_text(JdRequest(text=jd))
    if not resume_text:
        raise HTTPException(
            status_code=400,
            detail="Failed to extract readable text from the uploaded resume.",
        )

    return {
        "sessionId":sessionId,
        "resumeText":resume_text,
        "parseJd": parse_jd.page_content
    }

    
    
