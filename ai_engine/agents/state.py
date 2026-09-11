# agent/state.py
from typing import TypedDict, Optional, List, Dict, Any

class AgentState(TypedDict):
    # Inputs
    resume_id: str
    raw_resume: str
    raw_jd: str
    candidate_name: Optional[str]
    github_username: Optional[str]
    
    # Node 1 Outputs (Evaluator)
    ats_score: int
    score_breakdown: Dict[str, int]

    matched_skills: List[str]
    missing_skills: Dict[str, Any]   
    weak_verbs: List[Dict[str, Any]]
    formatting_alerts: List[str]

    requirement_analysis: List[Dict[str, Any]]   
    experience_evidence: List[Dict[str, Any]]   
    curation_signals: Dict[str, Any]            
    strategic_recommendation: str                
    
    # Node 2 Outputs (Rewriter + GitHub Analysis)
    tailored_bullets: List[str]
    project_recommendation_type: str  
    project_advice_message: str      
    
    # Node 3 Outputs (Generator)
    cover_letter: str
    cold_email: str
    linkedin_message: str
    generated_docx_url: Optional[str]
    generated_pdf_url: Optional[str]