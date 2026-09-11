import json
from dotenv import load_dotenv
import os , asyncio
# import logging
# logger = logging.getLogger("uvicorn")

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env"))
from google import genai
from google.genai import types
from ai_engine.agents.state import AgentState
from ai_engine.tools.github_tool import fetch_github_user_repos




REWRITER_PROMPT = """
You are an expert executive resume writer and career strategist.

Perform two tasks based on the provided inputs:

TASK 1: RESUME BULLET REWRITE
Select the most relevant 2–3 experience bullet points from the raw resume and rewrite them to incorporate missing target skills. 
- Mirror JD priorities without fabricating experience.
- Quantify impact where possible.
- DO NOT MAKE ANYTHING UP. Only use experience already present in the resume, positioning it better.
- If a bullet point lacks a clear metric or number, add quantifiable metric structures (e.g., increased efficiency by X%, managed Y team)

TASK 2: GITHUB & PROJECT ALIGNMENT ANALYSIS
Analyze the candidate's GitHub repositories against the Job Description:
- CASE A (Matching GitHub Projects): If any public repositories match missing skills required by the JD, identify them explicitly and explain how to add them to the resume. Do not invent repositories or technologies not present in the GitHub context.
- CASE B (No Matching GitHub Projects / No GitHub Provided): If GitHub projects do not match the JD, state that the resume should stick to existing listed projects. THEN, provide 2 concrete, realistic project build suggestions (including tech stack) that the candidate can build to bridge their JD skill gap. Suggestions must be realistic for the candidate’s experience level, using technologies already mentioned in the resume plus missing JD skills.

Target Missing Skills: 
{missing_skills}

Requirements Analysis:
{requirement_analysis}

Experience Evidence:
{experience_evidence}

GitHub Repository Context:
{github_context}

Raw Resume Text:
{raw_resume}

Job Description:
{raw_jd}

Return ONLY a valid JSON object with no commentary or markdown:
{
  "tailored_bullets": [
    "Rewritten bullet 1 featuring missing skill...",
    "Rewritten bullet 2 featuring missing skill..."
  ],
  "project_recommendation_type": "<'GITHUB_MATCH' or 'BUILD_SUGGESTION'>",
  "project_advice_message": "<Detailed suggestion message explaining which GitHub project to highlight OR what new project to build as per JD requirements>"
}
"""

def rewriter_bullets_node(state: AgentState)-> dict:

   

    github_context = "No GitHub username provided. Proceeding with resume bullet rewrite only."
    github_username = state.get("github_username")

    if github_username:
        try:
            repos = asyncio.run(fetch_github_user_repos(github_username))
            github_context = f"Public Repositories & Tech Stack: {repos}"

        except Exception as e:
            github_context = f"Could not fetch Github data: {str(e)}"


    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    prompt = REWRITER_PROMPT.format(
        missing_skills=json.dumps(state.get("missing_skills", {}), indent=2),
        requirement_analysis=json.dumps(state.get("requirement_analysis", []), indent=2),
        experience_evidence=json.dumps(state.get("experience_evidence", []), indent=2),
        github_context=github_context,
        raw_resume=state["raw_resume"],
        raw_jd=state["raw_jd"]
    )


    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.2
        )
    )

    result = json.loads(response.text)

    # print(f"rewritter node: {result}")
    # print("AgentState in rewritter  ",state)

    return {
    "tailored_bullets": result.get("tailored_bullets", []),
    "project_recommendation_type": result.get("project_recommendation_type", "BUILD_SUGGESTION"),
    "project_advice_message": result.get("project_advice_message", "")
    }
