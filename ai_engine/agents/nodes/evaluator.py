import json
import os
from google import genai
from google.genai import types
from agents.state import AgentState
from tools.deterministic_matcher import calculate_deterministic_metrics

EVALUATOR_PROMPT = """
You are a senior recruiter performing a 6-second initial scan and a deep ATS semantic analysis.

Analyze this candidate's resume against the target Job Description for:
1. GAP FINDER: Identify missing keywords, weak verbs, vague claims, and required skills not present.
2. RED FLAG SCAN: Identify cliché phrases, weak bullet structures, or anything that would cause a recruiter to skip this resume instantly.
3. SEMANTIC EXPERIENCE SCORE: Score candidate's overall experience depth against JD seniority (0-100).

Resume Text:
{raw_resume}

Job Description Text:
{raw_jd}

Return ONLY a valid JSON object:
{{
  "experience_score": <int 0-100 score based on seniority and experience fit>,
  "matched_skills": [<array of skills present in resume>],
  "missing_skills": [<array of JD skills missing in resume>],
  "weak_verbs": [<array of weak action verbs found>],
  "red_flags": [<array of clichés or instant skip triggers>]
}}
"""

def evaluate_ats_node(state: AgentState) -> dict:
    """NODE 1: Evaluates resume via Deterministic Engine + Gemini 2.5 Flash."""
    
    # 1. Run Deterministic Engine (spaCy + rapidfuzz)
    deterministic = calculate_deterministic_metrics(state["raw_resume"], state["raw_jd"])
    
    # 2. Run Gemini 2.5 Flash Engine
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    prompt = EVALUATOR_PROMPT.format(
        raw_resume=state["raw_resume"],
        raw_jd=state["raw_jd"]
    )
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.0  # Zero temperature for deterministic evaluation
        )
    )
    
    llm_result = json.loads(response.text)
    
    # 3. Compute Composite Score
    keyword_score = deterministic["exact_keyword_score"]
    exp_score = llm_result.get("experience_score", 50)
    fmt_score = 100 if not deterministic["missing_sections"] else 50
    
    final_score = int((keyword_score * 0.4) + (exp_score * 0.4) + (fmt_score * 0.2))
    
    # 4. Safely Merge Keywords (Exact Matches + Semantic Matches)
    combined_matched = list(set(deterministic["matched_keywords"] + llm_result.get("matched_skills", [])))
    combined_missing = list(set(deterministic["missing_keywords"] + llm_result.get("missing_skills", [])))
    
    # 5. Format Formatting Alerts
    formatting_alerts = [f"Missing standard section: {sec}" for sec in deterministic["missing_sections"]]
    formatting_alerts.extend(llm_result.get("red_flags", []))
    
    return {
        "ats_score": final_score,
        "score_breakdown": {
            "keyword_match_score": keyword_score,
            "experience_match_score": exp_score,
            "formatting_score": fmt_score
        },
        "matched_skills": combined_matched,
        "missing_skills": combined_missing,
        "weak_verbs": llm_result.get("weak_verbs", []),
        "formatting_alerts": formatting_alerts
    }