import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from ai_engine.agents.state import AgentState

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env"))

TAILOR_RESUME_PROMPT = """
You are a resume tailoring specialist.

Create a complete, structured JD-tailored resume from the original resume and job description.
Use the candidate's facts only. Never invent employers, dates, projects, technologies, metrics,
education, or achievements. You may rewrite wording and reorder sections to improve alignment
with the job description.

This is a transformation task, not a formatting or copying task. Do not return the original
resume verbatim. For every summary, experience bullet, project bullet, and skills line:
- Identify the closest JD requirement or responsibility.
- Rewrite the content to foreground that requirement using the candidate's existing evidence.
- Use the JD's terminology only when the resume supports the same skill or responsibility.
- Keep the original factual meaning, scope, and metrics accurate.
- Remove wording that is irrelevant to the JD only when the same factual coverage is preserved elsewhere.
Do check the weak Verb and Formatting alerts for professional curated structure and content to create a resume against the Job description

Original resume:
{raw_resume}

Job description:
{raw_jd}

ATS requirements and evidence:
{requirements}

Formatting Alerts:
{formatting_alerts}

Weak Verbs:
{weak_verbs}

Curation Signals:
{curation_signals}




Return ONLY valid JSON with this exact shape:
{{
  "name": "Candidate name",
  "contact": "Location | email | phone | LinkedIn | GitHub",
  "sections": [
    {{
      "title": "Professional Summary",
      "lines": ["One concise summary based only on the resume"]
    }},
    {{
      "title": "Skills",
      "lines": ["Languages: ...", "Frameworks: ..."]
    }},
    {{
      "title": "Experience",
      "lines": ["Role | Company | Dates", " JD-aligned bullet supported by the resume"]
    }},
    {{
      "title": "Projects",
      "lines": ["Project | technologies", " Project bullet 1 supported by the resume", " Project bullet 2 supported by the resume", " Project bullet 3 supported by the resume", " Project bullet 4 supported by the resume"]
    }},
    {{
      "title": "Education",
      "lines": ["Degree | Institution | Dates"]
    }},
    {{
      "title": "Certifications",
      "lines": ["Certification"]
    }},
    {{
      "title": "Achievements",
      "lines": ["Achievement"]
    }}
  ]
}}

Rules:
- Include only sections supported by the original resume.
- Use an empty sections array item only when it has real content; omit empty sections.
- Preserve every source project and every meaningful project detail from the original resume, but rewrite each detail for JD relevance.
- For each project, return 4-5 distinct, JD-aligned bullets when the original resume contains 4-5 or more meaningful details.
- If a project has fewer than 4 meaningful source details, preserve all available details; never invent bullets to reach 4-5.
- Do not combine multiple project details into one bullet when that would remove useful information.
- Every project bullet must communicate a technology, responsibility, implementation detail, or measurable outcome relevant to the JD.
- Do not copy a raw project sentence unchanged unless it is already precise, JD-relevant, and grammatically strong.
- Keep the section titles exactly as shown where applicable.
- Preserve important factual details while prioritizing JD-relevant evidence.
- In experience section if user has done a opensource contribution do include that inside experience section as heading of Open Sorce Contribution
"""


def _json_prompt(state: AgentState) -> str:
    requirements = {
        "matched_skills": state.get("matched_skills", []),
        "missing_skills": state.get("missing_skills", {}),
        "requirement_analysis": state.get("requirement_analysis", []),
        "experience_evidence": state.get("experience_evidence", []),
    }

    prompt = TAILOR_RESUME_PROMPT.format(
        requirements=json.dumps(requirements,indent=2),
        raw_resume=state["raw_resume"],
        raw_jd=state["raw_jd"],
        formatting_alerts=json.dumps(state.get("formatting_alerts",[]),indent=2),
        weak_verbs=json.dumps(state.get("weak_verbs" ,[]),indent=2),
        curation_signals=json.dumps(state.get("curation_signals", {}),indent=2)
    )
    return prompt



def _normalize_result(result: dict) -> dict:
    sections = []
    for section in result.get("sections", []):
        title = str(section.get("title", "")).strip()
        lines = [str(line).strip() for line in section.get("lines", []) if str(line).strip()]
        if title and lines:
            sections.append({"title": title, "lines": lines})
    return {
        "name": str(result.get("name", "Candidate")).strip() or "Candidate",
        "contact": str(result.get("contact", "")).strip(),
        "sections": sections,
    }


def tailor_resume_node(state: AgentState) -> dict:
    """Build the complete JD-aligned resume consumed by the exporter."""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=_json_prompt(state),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )
    tailored_resume = _normalize_result(json.loads(response.text))
    print("Tailored resume structure:", tailored_resume)
    return {"tailored_resume": tailored_resume}
