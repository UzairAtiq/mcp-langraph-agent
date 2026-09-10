import os 
from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROK_API_KEY")
DATABASE_URL = os.getenv("CONNECTION_STRING_SUPABASE")