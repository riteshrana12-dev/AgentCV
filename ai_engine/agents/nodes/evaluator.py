import json
from dotenv import load_dotenv
import os
# import logging
# logger = logging.getLogger("uvicorn")
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env"))
from google import genai
from google.genai import types
from ai_engine.agents.state import AgentState
from ai_engine.tools.deterministic_matcher import calculate_deterministic_metrics
from ai_engine.tools.flatten_tailored_resume import _flatten_tailored_resume
from ai_engine.agents.system_prompts.evaluator_prompt import EVALUATOR_PROMPT

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
        model="gemini-3.5-flash-lite",
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
    combined_missing = {
        "truly_missing": llm_result.get("missing_skills", {}).get("truly_missing", []),
        "partially_supported": llm_result.get("missing_skills", {}).get("partially_supported", [])
    }
    
    # 5. Format Formatting Alerts
    formatting_alerts = [f"Missing standard section: {sec}" for sec in deterministic["missing_sections"]]
    red_flags = llm_result.get("red_flags", [])
    formatting_alerts.extend([rf["issue"] for rf in red_flags if isinstance(rf, dict) and "issue" in rf])

# Pretty-print JSON in logs

    # result_payload= {
    #         "ats_score": final_score,
    #         "score_breakdown": {
    #             "keyword_match_score": keyword_score,
    #             "experience_match_score": exp_score,
    #             "formatting_score": fmt_score
    #         },
    #         "matched_skills": combined_matched,
    #         "missing_skills": combined_missing,
    #         "weak_verbs": llm_result.get("weak_verbs", []),
    #         "formatting_alerts": formatting_alerts,
    #         "requirement_analysis": llm_result.get("requirement_analysis", []),
    #         "experience_evidence": llm_result.get("experience_evidence", []),
    #         "curation_signals": llm_result.get("curation_signals", {}),
    #         "strategic_recommendation": llm_result.get("strategic_recommendation", "")
    #     }

    # print("evaluatornode",result_payload )
    # logger.info("Resume evaluation result:\n%s", json.dumps(result_payload, indent=2))

    # print("AgentState in evaluator  ",state)

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
        "formatting_alerts": formatting_alerts,
        "requirement_analysis": llm_result.get("requirement_analysis", []),
        "experience_evidence": llm_result.get("experience_evidence", []),
        "curation_signals": llm_result.get("curation_signals", {}),
        "strategic_recommendation": llm_result.get("strategic_recommendation", "")
    }


def re_evaluate_tailored_ats_node(state: AgentState) -> dict:
    """NODE 4: Re-evaluates tailored JSON resume content to measure ATS score improvement."""
    
    tailored_data = state.get("tailored_resume", {})
    
    # Convert structured dictionary into a plain string format
    tailored_text = _flatten_tailored_resume(tailored_data)
    
    if not tailored_text:
        # Fallback to raw resume if tailored text generation failed
        tailored_text = state.get("raw_resume", "")

    # 1. Run deterministic matcher on updated text
    deterministic = calculate_deterministic_metrics(tailored_text, state["raw_jd"])
    
    # 2. Dynamic Keyword Score from the updated document
    keyword_score = deterministic["exact_keyword_score"]
    
    # 3. Dynamic experience calculation based on resolved missing skills
    baseline_exp_score = state.get("score_breakdown", {}).get("experience_match_score", 50)
    truly_missing = state.get("missing_skills", {}).get("truly_missing", [])
    
    resolved_count = sum(1 for skill in truly_missing if str(skill).lower() in tailored_text.lower())
    skill_boost = resolved_count * 10
    improved_exp_score = min(100, baseline_exp_score + skill_boost)
    
    # 4. Dynamic formatting score check
    fmt_score = 100 if not deterministic["missing_sections"] else 50
    
    # 5. Calculate Composite Score for Tailored Resume
    tailored_final_score = int((keyword_score * 0.4) + (improved_exp_score * 0.4) + (fmt_score * 0.2))

    return {
        "tailored_ats_score": tailored_final_score,
        "tailored_score_breakdown": {
            "keyword_match_score": keyword_score,
            "experience_match_score": improved_exp_score,
            "formatting_score": fmt_score
        }
    }