from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ai_engine.routers import resume_route
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://172.27.64.1:3001"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume_route.router)