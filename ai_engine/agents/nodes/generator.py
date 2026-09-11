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
from ai_engine.tools.exporter import export_docx, export_pdf


GENERATOR_PROMPT = """
You are an elite career strategist and application-writing specialist.

Your job is NOT to simply summarize the candidate's resume.

Your job is to analyze the relationship between:

1. The Job Description
2. The candidate's actual resume experience
3. Skills that match the JD
4. Skills that are missing from the candidate's profile

Then create three highly curated outreach assets that are specifically tailored to THIS job.

========================
CANDIDATE-JOB ANALYSIS
======================

Matched Skills:
{matched_skills}

Missing Skills:
{missing_skills}

Strategic Recommendation:
{strategic_recommendation}

Strongest Evidence:
{strongest_candidate_evidence}

Best Projects:
{best_projects_to_highlight}

Job Description:
{raw_jd}

Resume:
{raw_resume}

========================
CORE INSTRUCTIONS
=================

1. PRIORITIZE THE JOB DESCRIPTION

First identify the most important requirements, responsibilities, technologies, and qualities in the JD.

Do not treat every keyword equally.

Prioritize:

* Core technical requirements
* Responsibilities
* Directly relevant experience
* Important soft skills
* Technologies explicitly requested by the employer

2. CONNECT JD REQUIREMENTS TO REAL EXPERIENCE

For each important JD requirement, find the strongest supporting evidence from the candidate's resume.

Prefer concrete evidence such as:

* Real projects
* Internship/work experience
* Production systems
* Open-source contributions
* Specific technologies used
* Problems solved
* Measurable outcomes

Do NOT invent experience.

Do NOT claim the candidate has a skill merely because a related skill exists.

3. HANDLE MISSING SKILLS CAREFULLY

Missing skills must NOT be falsely presented as candidate experience.

If a skill is missing but the candidate has adjacent/relevant experience, position it honestly as transferable knowledge.

Example:

Bad:
"I have extensive experience with Angular."

If Angular is missing.

Good:
"My experience with React.js and Node.js has given me a strong foundation in modern web development, and I am eager to apply that foundation while learning Angular."

4. CURATE, DON'T DUMP

Do not mention every technology from the resume.

Select only the experiences and technologies that strengthen the candidate's case for THIS specific job.

Generally use the strongest 2–4 relevant experiences rather than listing the entire resume.

5. USE EVIDENCE

Whenever possible, connect a claim to a concrete candidate experience.

Instead of:

"I am experienced in backend development."

Prefer:

"I built backend systems using Node.js and Express.js, including REST APIs and database integrations."

Only make claims supported by the resume.

6. AVOID GENERIC AI-SOUNDING LANGUAGE

Avoid phrases such as:

* "I am thrilled to apply..."
* "I am confident that I would be a great fit..."
* "I am passionate about..."
* "hit the ground running"
* "leverage my skills"
* "dynamic environment"
* "exciting opportunity"
* "valuable opportunity"
* "highly motivated individual"

unless the wording is genuinely necessary.

Write naturally, specifically, and professionally.

7. DIFFERENTIATE THE THREE ASSETS

Each asset has a different purpose.

---

## COVER LETTER

Purpose:
Build a strong argument for why the candidate is relevant to the role.

Structure:

* Opening: specific interest in the role
* 1–2 strongest candidate experiences relevant to the JD
* Connect technical skills to actual responsibilities
* Address relevant strengths/transferable skills
* Close professionally

Target:
Approximately 250–400 words.

Do not repeat the resume line-by-line.

---

## COLD EMAIL

Purpose:
Get the recruiter's/hiring team's attention quickly.

Structure:

* Strong subject line
* Short introduction
* Why this specific role
* 1–2 strongest relevant qualifications
* Clear reason the candidate is worth considering
* Simple call to action

Target:
Approximately 120–200 words.

Keep it concise.

---

## LINKEDIN MESSAGE

Purpose:
Start a conversation, NOT submit the entire application.

Structure:

* Personalized opening
* Mention the specific role
* Mention 1–2 highly relevant candidate strengths
* Short reason for reaching out
* Simple conversational CTA

Target:
Approximately 50–100 words.

Do not include the entire resume.

========================
PERSONALIZATION RULES
=====================

The generated content should feel specifically written for the provided JD.

Where appropriate:

* Mirror important terminology from the JD
* Reference the employer's responsibilities
* Connect candidate experience directly to those responsibilities
* Highlight the most relevant projects
* Mention relevant technologies only when they strengthen the argument

Do not keyword-stuff.

Do not copy sentences from the JD.

Do not fabricate company information, recruiter names, achievements, responsibilities, technologies, or experience.

If the hiring manager's name is unavailable, use "Hiring Manager".

========================
CONSISTENCY RULES
=================

All three assets must be based on the same candidate facts.

Do not introduce a skill in the cover letter that is not supported by the resume.

Do not introduce a project in the LinkedIn message that was not mentioned or supported by the resume.

Do not contradict the candidate's experience.

========================
OUTPUT FORMAT
=============

Return ONLY valid JSON.

Do not include markdown.
Do not include ```json.
Do not include explanations before or after the JSON.

Return exactly:

{
"cover_letter": "...",
"cold_email": "...",
"linkedin_message": "..."
}
"""



def generate_docs_node(state: AgentState)-> dict:

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    


    prompt = GENERATOR_PROMPT.format(
        matched_skills=json.dumps(state.get("matched_skills", []), indent=2),
        missing_skills=json.dumps(state.get("missing_skills", {}), indent=2),
        requirement_analysis=json.dumps(state.get("requirement_analysis", []), indent=2),
        strategic_recommendation=state.get("strategic_recommendation", ""),
        strongest_candidate_evidence=json.dumps(
            state.get("curation_signals", {}).get("strongest_candidate_evidence", []),
            indent=2
        ),
        best_projects_to_highlight=json.dumps(
            state.get("curation_signals", {}).get("best_projects_to_highlight", []),
            indent=2
        ),
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
    tailored_bullets = state.get("tailored_bullets",[])
    candidate_name = state.get("candidate_name","Candidate")
    
    
    # generated output files

    docx_bytes = export_docx(
        candidate_name=candidate_name,
        bullets=tailored_bullets,
        raw_resume=state["raw_resume"],
    )

    pdf_bytes = export_pdf(
        candidate_name=candidate_name,
        bullets=tailored_bullets,
        raw_resume=state["raw_resume"],
    )



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