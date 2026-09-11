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

EVALUATOR_PROMPT = """
You are a senior technical recruiter, ATS analyst, and resume screening specialist.

Your task is to perform a structured analysis of a candidate's resume against a target Job Description.

Do NOT rewrite the resume.

Your job is to identify:

* What the JD requires
* What the candidate actually has
* What is missing
* Which candidate experiences provide evidence for the requirements
* Which requirements are most important
* What should be highlighted later by the rewriting/generation agents

You must base every conclusion on the provided resume and JD.

Do NOT invent skills, experience, projects, responsibilities, achievements, technologies, or employers.

# ======================== INPUT

Resume:
{raw_resume}

Job Description:
{raw_jd}

# ========================

1. REQUIREMENT ANALYSIS

# ========================

Extract the important requirements from the JD.

For each important requirement determine:

* requirement
* category
* importance
* candidate_match
* evidence_from_resume

Categories may include:

* technical_skill
* framework
* database
* backend
* frontend
* tooling
* responsibility
* soft_skill
* experience
* education
* other

Importance:

* high
* medium
* low

candidate_match:

* strong
* partial
* missing

Evidence must refer to actual resume content.

Example:

{
"requirement": "PostgreSQL database schemas and queries",
"category": "database",
"importance": "high",
"candidate_match": "strong",
"evidence_from_resume": [
"Candidate's project uses PostgreSQL",
"Resume describes PostgreSQL persistence"
]
}

# ========================

2. MATCHED SKILLS

# ========================

Identify skills explicitly present in the resume that are relevant to the JD.

Do not include generic words such as:

* code
* web
* experience
* applications
* features
* problem
* end

unless the JD specifically requires that exact concept as a meaningful skill.

Prefer normalized technical skills such as:

* React.js
* Node.js
* Express.js
* PostgreSQL
* JavaScript
* TypeScript
* Git
* GitHub
* REST APIs

Avoid duplicates caused by capitalization.

For example:

"javascript", "JavaScript" → "JavaScript"

# ========================

3. MISSING SKILLS

# ========================

Identify meaningful JD requirements that are not supported by the resume.

Only include actual requirements from the JD.

Do NOT classify generic JD words such as:

* month
* location
* INR
* responsibilities
* world

as missing skills.

Separate missing skills into:

* truly_missing
* partially_supported

Example:

{
"truly_missing": [
"Angular",
"Vue"
],
"partially_supported": [
{
"skill": "Git/GitHub workflows",
"related_experience": "Candidate has GitHub and collaborative development experience",
"gap": "Specific workflow or collaboration process is not explicitly described"
}
]
}

# ========================

4. EXPERIENCE EVIDENCE

# ========================

Identify the strongest candidate experiences that support the JD.

For each experience include:

* source
* relevant_requirement
* evidence
* relevance_score (0-100)

The "source" should identify the relevant experience using only information available in the resume.

Examples of valid source descriptions:

* "Candidate's internship experience"
* "Candidate's backend project"
* "Candidate's full-stack project"
* "Candidate's open-source contribution"
* "Candidate's academic project"

Do not invent or rename experiences.

Example:

{
"source": "Candidate's backend project",
"relevant_requirement": "PostgreSQL",
"evidence": "Project uses PostgreSQL for data persistence",
"relevance_score": 92
}

# ========================

5. EXPERIENCE SCORE

# ========================

Calculate:

experience_score: 0-100

This score should measure how well the candidate's actual experience matches the JD's required level and responsibilities.

Consider:

* years/type of experience
* internship experience
* project depth
* production experience
* technical responsibility
* relevance to JD
* complexity of work
* evidence strength

Do NOT inflate the score simply because the candidate has many technologies.

# ========================

6. WEAK VERBS

# ========================

Identify weak or repetitive action verbs used in resume bullets.

Only report verbs that genuinely weaken the bullet.

Examples may include:

* Fixed
* Worked
* Helped
* Assisted
* Used
* Built

Do NOT automatically classify every common verb as weak.

Also provide a stronger alternative when appropriate.

Example:

{
"verb": "Fixed",
"suggested_alternatives": [
"Resolved",
"Diagnosed",
"Remediated"
]
}

# ========================

7. RED FLAGS

# ========================

Identify issues that could negatively affect recruiter perception or ATS quality.

Look for:

* clichés
* vague claims
* unsupported claims
* repetitive wording
* keyword stuffing
* unnecessary technologies
* weak bullet construction
* missing measurable impact
* inconsistent dates
* suspicious/future dates
* formatting concerns visible from the supplied text
* overly generic summary statements

For each red flag provide:

* issue
* severity
* evidence
* recommendation

Severity:

* high
* medium
* low

Do not invent formatting problems that cannot be determined from plain text.

# ========================

8. CURATION SIGNALS

# ========================

Identify the most important information that a later rewriting/generation agent should emphasize.

Return:

* top_requirements
* strongest_candidate_evidence
* best_projects_to_highlight
* transferable_skills
* skills_or_experiences_to_avoid_highlighting

Example:

{
"top_requirements": [
"React.js",
"Node.js",
"PostgreSQL"
],
"strongest_candidate_evidence": [
"Candidate's relevant internship experience",
"Candidate's backend project using PostgreSQL"
],
"best_projects_to_highlight": [
"Candidate's backend project"
],
"transferable_skills": [
{
"jd_requirement": "Angular/Vue",
"candidate_skill": "React.js",
"reason": "Frontend framework experience is transferable"
}
],
"skills_or_experiences_to_avoid_highlighting": [
"Technologies unrelated to the target role"
]
}

# ========================

9. FINAL RECOMMENDATION

# ========================

Provide a short strategic recommendation for the next agent.

Explain:

* What is the candidate's strongest selling point for this JD?
* What is the biggest gap?
* Which 2–4 experiences should be prioritized?
* What should NOT be exaggerated or claimed?

# ========================

OUTPUT

# ========================

Return ONLY valid JSON.

Do not include markdown.
Do not include ```json.
Do not include explanations outside the JSON.

Return exactly this structure:

{
"experience_score": 0,

"requirement_analysis": [],

"matched_skills": [],

"missing_skills": {
"truly_missing": [],
"partially_supported": []
},

"experience_evidence": [],

"weak_verbs": [],

"red_flags": [],

"curation_signals": {
"top_requirements": [],
"strongest_candidate_evidence": [],
"best_projects_to_highlight": [],
"transferable_skills": [],
"skills_or_experiences_to_avoid_highlighting": []
},

"strategic_recommendation": ""
}
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