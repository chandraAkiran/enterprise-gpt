import os
from pathlib import Path

from dotenv import load_dotenv


# Load .env
load_dotenv()


# -----------------------------------------
# Base directories
# -----------------------------------------

BASE_DIR = Path(__file__).resolve().parent

DOCUMENT_DIR = BASE_DIR / "documents"

VECTOR_DIR = BASE_DIR / "vector_db"


DOCUMENT_DIR.mkdir(exist_ok=True)

VECTOR_DIR.mkdir(exist_ok=True)


# -----------------------------------------
# Gemini
# -----------------------------------------

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

GEMINI_MODEL = "gemini-3.6-flash"

EMBEDDING_MODEL = "gemini-embedding-2"


# -----------------------------------------
# Supabase
# -----------------------------------------

SUPABASE_URL = os.getenv(
    "SUPABASE_URL"
)

SUPABASE_SECRET_KEY = os.getenv(
    "SUPABASE_SECRET_KEY"
)


# -----------------------------------------
# RAG settings
# -----------------------------------------

CHUNK_SIZE = 1000

CHUNK_OVERLAP = 200

TOP_K = 5
