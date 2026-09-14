def _flatten_tailored_resume(tailored_resume: dict) -> str:
    """Helper function to convert structured JSON resume back into plain text for NLP evaluation."""
    if not isinstance(tailored_resume, dict):
        return str(tailored_resume)

    text_parts = [
        str(tailored_resume.get("name", "")).strip(),
        str(tailored_resume.get("contact", "")).strip()
    ]
    
    for section in tailored_resume.get("sections", []):
        title = str(section.get("title", "")).strip()
        lines = section.get("lines", [])
        
        # Ensure lines are non-empty and converted safely to strings
        valid_lines = [str(line).strip() for line in lines if str(line).strip()]
        
        if title and valid_lines:
            text_parts.append(f"\n### {title.upper()}")
            text_parts.extend(valid_lines)

    return "\n".join(part for part in text_parts if part).strip()