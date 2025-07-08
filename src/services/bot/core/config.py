import os
from dotenv import load_dotenv

load_dotenv()

BOT_STORAGE_SESSION_FOLDER = "./sessions"
RAPID_API_INSTAGRAM_HOST = os.getenv("RAPID_API_INSTAGRAM_HOST")
RAPID_API_KEY = os.getenv("RAPID_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
RABBIT_MQ_HOST = os.getenv("RABBIT_MQ_HOST", "")
RABBIT_MQ_PORT = os.getenv("RABBIT_MQ_PORT", "")
RABBIT_MQ_USERNAME = os.getenv("RABBIT_MQ_USERNAME", "")
RABBIT_MQ_PASSWORD = os.getenv("RABBIT_MQ_PASSWORD", "")
