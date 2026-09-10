import re
from rapidfuzz import fuzz
import spacy
import logging
logger = logging.getLogger("uvicorn")

nlp = spacy.load("en_core_web_sm")

REQUIRED_SECTIONS = ["experience", "education", "skills", "professional summary", "projects"]

def extract_tokens(text: str) -> set:
    """Extracts clean noun/propn tokens from text (e.g., Python, Docker, PostgreSQL)."""
    doc = nlp(text.lower())
    return {
        token.text for token in doc 
        if token.pos_ in ["NOUN", "PROPN"] and not token.is_stop and len(token.text) > 2
    }

def calculate_deterministic_metrics(raw_resume: str, raw_jd: str) -> dict:
    """
    Computes exact keyword overlap and formatting constraints deterministically.
    """
    resume_lower = raw_resume.lower()
    jd_tokens = extract_tokens(raw_jd)
    resume_tokens = extract_tokens(raw_resume)

    # 1. Exact Keyword Overlap
    matched_keywords = list(jd_tokens.intersection(resume_tokens))
    missing_keywords = list(jd_tokens.difference(resume_tokens))
    keyword_match_ratio = len(matched_keywords) / max(len(jd_tokens), 1)

    # 2. Section Header Validation
    missing_sections = []
    for section in REQUIRED_SECTIONS:
        if not re.search(r'\b' + section + r'\b', resume_lower):
            missing_sections.append(section.capitalize())

    # 3. Overall Text Fuzzy Similarity Ratio
    fuzzy_score = fuzz.token_set_ratio(raw_resume, raw_jd)


    logger.info(f"""
                "exact_keyword_score": {round(keyword_match_ratio * 100)},
                "fuzzy_similarity": {fuzzy_score},
                "matched_keywords": {matched_keywords[:15]},
                "missing_keywords": {missing_keywords[:15]},
                "missing_sections": {missing_sections}
              """)

    return {
        "exact_keyword_score": round(keyword_match_ratio * 100),
        "fuzzy_similarity": fuzzy_score,
        "matched_keywords": matched_keywords[:15],
        "missing_keywords": missing_keywords[:15],
        "missing_sections": missing_sections
    }