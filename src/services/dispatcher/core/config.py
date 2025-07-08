import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
RABBIT_MQ_HOST = os.getenv("RABBIT_MQ_HOST", "")
RABBIT_MQ_PORT = os.getenv("RABBIT_MQ_PORT", "")
RABBIT_MQ_USERNAME = os.getenv("RABBIT_MQ_USERNAME", "")
RABBIT_MQ_PASSWORD = os.getenv("RABBIT_MQ_PASSWORD", "")
