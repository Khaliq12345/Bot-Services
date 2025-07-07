import os
from dotenv import load_dotenv

load_dotenv()

RAPID_API_INSTAGRAM_HOST = os.getenv("RAPID_API_INSTAGRAM_HOST")
RAPID_API_KEY = os.getenv("RAPID_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
