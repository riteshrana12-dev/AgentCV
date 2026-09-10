from pydantic import BaseModel, Field
from typing import Optional

class TailorResumeRequest(BaseModel):
    storage_path: str
    file_name: str
    jd: str = Field(..., description="Job description text to tailor the resume for")
    github_username: Optional[str] = Field(None, description="GitHub username for additional context")
    resume_id: str
    callback_url: str = Field(..., description="Callback URL to send the results after processing")



class JdRequest(BaseModel):
    text: str = Field(...,description="Job description text")
