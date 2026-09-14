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
from ai_engine.agents.system_prompts.rewriter_prompt import REWRITER_PROMPT



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
