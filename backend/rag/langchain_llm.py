from langchain_google_genai import (
    ChatGoogleGenerativeAI
)

from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL
)


# ==========================================
# LANGCHAIN GEMINI LLM
# ==========================================

llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GEMINI_API_KEY,
    temperature=0
)


def test_langchain_llm():

    response = llm.invoke(
        "Reply with exactly: "
        "LangChain Gemini connection successful"
    )

    return response.content


# ==========================================
# LOCAL TEST
# ==========================================

if __name__ == "__main__":

    result = test_langchain_llm()

    print(result)
