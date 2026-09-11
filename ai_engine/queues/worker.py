from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
import asyncio
import requests
from rq import Queue
from redis import Redis
import logging

from ai_engine.agents.graph import compiled_workflow

logger = logging.getLogger("uvicorn")

redis_conn = Redis(host="localhost", port=6379, decode_responses=True)
queue = Queue("resume_tailoring", connection=redis_conn)

def enqueue_resume_tailoring_task(state: dict, callback_url: str):
    result_state = asyncio.run(compiled_workflow.ainvoke(state))

    payload = {
        "resume_id": result_state["resume_id"],
        "ats_score": result_state["ats_score"],
        "score_breakdown": result_state["score_breakdown"],
        "matched_skills": result_state["matched_skills"],
        "missing_skills": result_state["missing_skills"],
        "weak_verbs": result_state["weak_verbs"],
        "formatting_alerts": result_state["formatting_alerts"],
        "requirement_analysis": result_state["requirement_analysis"],
        "experience_evidence": result_state["experience_evidence"],
        "curation_signals": result_state["curation_signals"],
        "strategic_recommendation": result_state["strategic_recommendation"],
        "tailored_bullets": result_state["tailored_bullets"],
        "project_recommendation_type": result_state["project_recommendation_type"],
        "project_advice_message": result_state["project_advice_message"],
        "cover_letter": result_state["cover_letter"],
        "cold_email": result_state["cold_email"],
        "linkedin_message": result_state["linkedin_message"],
        "generated_docx_url": result_state["generated_docx_url"],
        "generated_pdf_url": result_state["generated_pdf_url"],
    }

    logger.info(
        "Worker result: resume_id=%s ats_score=%s docx_url=%s pdf_url=%s",
        payload["resume_id"],
        payload["ats_score"],
        payload["generated_docx_path"],
        payload["generated_pdf_path"],
    )
    response = requests.post(callback_url, json=payload, timeout=30)
    response.raise_for_status()


    return payload



