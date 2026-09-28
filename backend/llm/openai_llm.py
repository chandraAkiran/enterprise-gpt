import os

from langchain_openai import ChatOpenAI


# =====================================================
# OPENAI CONFIGURATION
# =====================================================

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY"
)


# =====================================================
# CREATE OPENAI LLM
# =====================================================

def create_openai_llm():

    if not OPENAI_API_KEY:

        raise ValueError(
            "OPENAI_API_KEY is not configured."
        )

    return ChatOpenAI(
        model="gpt-5.4-mini",
        api_key=OPENAI_API_KEY,
        temperature=0,
    )
