from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_engine.routers import resume_route
from ai_engine.routers import interview_route
from ai_engine.agents.interview_agent.router import router as interview_agent_router

app = FastAPI()

cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume_route.router)
app.include_router(interview_route.router)
app.include_router(interview_agent_router)
