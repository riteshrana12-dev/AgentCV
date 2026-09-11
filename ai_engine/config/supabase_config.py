import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client

env_file = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_file)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL:
    raise RuntimeError(f"SUPABASE_URL is missing from: {env_file}")

if not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError(f"SUPABASE_SERVICE_ROLE_KEY is missing from: {env_file}")

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
)