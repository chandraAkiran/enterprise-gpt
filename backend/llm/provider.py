# =====================================================
# LLM PROVIDER
# =====================================================

from rag.langchain_llm import (
    llm as gemini_llm
)

from llm.openai_llm import (
    create_openai_llm
)


# =====================================================
# SUPPORTED PROVIDERS
# =====================================================

SUPPORTED_PROVIDERS = [
    "gemini",
    "openai",
]


# =====================================================
# GET LLM
# =====================================================

def get_llm(
    provider: str = "gemini",
):

    provider = provider.lower().strip()


    # -------------------------------------------------
    # Gemini
    # -------------------------------------------------

    if provider == "gemini":

        return gemini_llm


    # -------------------------------------------------
    # OpenAI
    # -------------------------------------------------

    if provider == "openai":

        return create_openai_llm()


    # -------------------------------------------------
    # Unsupported provider
    # -------------------------------------------------

    raise ValueError(
        f"Unsupported LLM provider: {provider}"
    )
