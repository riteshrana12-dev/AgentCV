GENERATOR_PROMPT = """
You are an elite career strategist. Generate three outreach assets based on candidate data and job details:

Matched Skills: {matched_skills}
Missing Skills: {missing_skills}
Job Description: {raw_jd}
Resume Context: {raw_resume}

This below output the cover_letter , cold_email and linkedin_message this three it should be in professional outreach way .

Return ONLY a JSON object:
{{
  "cover_letter": "To, Hiring Manager,...",
  "cold_email": "Subject: ...\\n\\nHi [Hiring Manager],...",
  "linkedin_message": "Hi [Name], I noticed your team..."
}}
"""