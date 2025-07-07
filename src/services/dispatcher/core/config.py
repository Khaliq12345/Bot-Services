import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
