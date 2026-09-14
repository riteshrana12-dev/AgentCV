
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
{{
  "tailored_bullets": [
    "Rewritten bullet 1 featuring missing skill...",
    "Rewritten bullet 2 featuring missing skill..."
  ],
  "project_recommendation_type": "<'GITHUB_MATCH' or 'BUILD_SUGGESTION'>",
  "project_advice_message": "<Detailed suggestion message explaining which GitHub project to highlight OR what new project to build as per JD requirements>"
}}
"""
