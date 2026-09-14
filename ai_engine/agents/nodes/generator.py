import json 
from dotenv import load_dotenv
import os
import logging
logger = logging.getLogger("uvicorn")
from uuid import uuid4
from ai_engine.config.supabase_config import supabase

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env"))
from google import genai
from google.genai import types
from ai_engine.agents.state import AgentState
from ai_engine.tools.exporter import ExportResumeData, ResumeSection, export_docx, export_pdf
from ai_engine.agents.system_prompts.generator_prompt import GENERATOR_PROMPT




def generate_docs_node(state: AgentState)-> dict:

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    


    prompt = GENERATOR_PROMPT.format(
        matched_skills = json.dumps(state.get("matched_skills",[])),
        missing_skills = json.dumps(state.get("missing_skills",[])),
        raw_jd=state["raw_jd"],
        raw_resume=state["raw_resume"]
    )

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.4
        )
    )

    result = json.loads(response.text)
    tailored_resume = state.get("tailored_resume", {})
    if not tailored_resume or not tailored_resume.get("sections"):
        raise ValueError("tailor_resume node returned no structured resume sections")

    sections_by_title: dict[str, ResumeSection] = {}
    for section in tailored_resume["sections"]:
        title = str(section.get("title", "")).strip()
        lines = [str(line).strip() for line in section.get("lines", []) if str(line).strip()]
        if not title or not lines:
            continue
        if title not in sections_by_title:
            sections_by_title[title] = ResumeSection(title=title, lines=[])
        sections_by_title[title].lines.extend(lines)

    if not sections_by_title:
        raise ValueError("tailor_resume node returned only empty sections")

    resume_data = ExportResumeData(
        name=tailored_resume.get("name") or state.get("candidate_name") or "Candidate",
        contact=tailored_resume.get("contact", ""),
        sections=list(sections_by_title.values()),
    )

    logger.info(
        "Exporting tailored resume: sections=%s lines=%d",
        list(sections_by_title),
        sum(len(section.lines) for section in resume_data.sections),
    )
    
    
    # generated output files

    docx_bytes = export_docx(data=resume_data)

    pdf_bytes = export_pdf(data=resume_data)



    resume_id = state["resume_id"]

    docx_storage_path = f"tailored/{resume_id}-{uuid4()}.docx"
    pdf_storage_path = f"tailored/{resume_id}-{uuid4()}.pdf"

    try:
        supabase.storage.from_("resumes").upload(
            docx_storage_path,
            docx_bytes,
            {"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
        )
        logger.info("Uploaded tailored DOCX: path=%s bytes=%d", docx_storage_path, len(docx_bytes))

        supabase.storage.from_("resumes").upload(
            pdf_storage_path,
            pdf_bytes,
            {"content-type": "application/pdf"},
        )
        logger.info("Uploaded tailored PDF: path=%s bytes=%d", pdf_storage_path, len(pdf_bytes))
    except Exception:
        logger.exception("Failed to upload tailored resume files to Supabase Storage")
        raise

    docx_public_url = supabase.storage.from_("resumes").get_public_url(
        docx_storage_path
    )

    pdf_public_url = supabase.storage.from_("resumes").get_public_url(
        pdf_storage_path
    )

    node_result = {
        "cover_letter": result.get("cover_letter", ""),
        "cold_email": result.get("cold_email", ""),
        "linkedin_message": result.get("linkedin_message", ""),
        "generated_docx_url": docx_public_url,
        "generated_pdf_url": pdf_public_url,
    }

    # print("AgentState in generator  ",state)

    # print("Generator node completed: %s", node_result)
    return node_result