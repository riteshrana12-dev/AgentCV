import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from ai_engine.agents.state import AgentState
from ai_engine.agents.system_prompts.tailor_resume_prompt import TAILOR_RESUME_PROMPT

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env"))

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
