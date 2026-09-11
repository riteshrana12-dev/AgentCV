from fastapi import HTTPException

from ai_engine.config.supabase_config import supabase

def get_file_bytes_from_supabase(storage_path: str) -> bytes:

    try:
        return supabase.storage.from_("resumes").download(storage_path)
        

    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Error fetching file from Supabase: {str(error)}")