from fastapi import APIRouter, HTTPException
from ai_engine.schemas.resume_schema import TailorResumeRequest, JdRequest
from ai_engine.services.resume_bytes import get_file_bytes_from_supabase
from ai_engine.services.resume_service import _extract_raw_text
from ai_engine.queues.worker import enqueue_resume_tailoring_task, queue
from ai_engine.tools.jd_parser import job_description_text
import logging
logger = logging.getLogger("uvicorn")


router = APIRouter(prefix="/resume", tags=["Resume Tailoring"])

@router.post("/tailor_resume")
async def tailor_resume(req: TailorResumeRequest):
    logger.info(f"storage path: {req.storage_path}")
    file_bytes = get_file_bytes_from_supabase(req.storage_path)

    if not file_bytes:
        return {"error": "Failed to fetch the resume from Supabase."}

    # Extract raw text from the resume
    resume_text,_file_type  = _extract_raw_text(file_bytes, req.file_name)
    parse_jd = job_description_text(JdRequest(text=req.jd))
    if not resume_text:
        raise HTTPException(status_code=400, detail="Failed to extract text from the resume.")

    state = {
        "resume_id": req.resume_id,
        "raw_resume": resume_text,
        "raw_jd": parse_jd.page_content,
         "candidate_name": None,
        "github_username": req.github_username,
        "ats_score": 0,
        "score_breakdown": {},
        "matched_skills": [],
        "missing_skills": [],
        "weak_verbs": [],
        "formatting_alerts": [],
        "tailored_bullets": [],
        "project_recommendation_type": "",
        "project_advice_message": "",
        "cover_letter": "",
        "cold_email": "",
        "linkedin_message": "",
        "generated_docx_url": None,
        "generated_pdf_url": None,
    }

    job = queue.enqueue(enqueue_resume_tailoring_task, state, req.callback_url)
    return {"status": "queued", "job_id": job.id,
        "resume_id": req.resume_id,}


   
        

    

