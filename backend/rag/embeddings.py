from google import genai
from google.genai import types

from config import (
    GEMINI_API_KEY,
    EMBEDDING_MODEL
)


client = genai.Client(
    api_key=GEMINI_API_KEY
)


def generate_embedding(text):

    result = client.models.embed_content(

        model=EMBEDDING_MODEL,

        contents=text,

        config=types.EmbedContentConfig(
            output_dimensionality=768
        )
    )

    return result.embeddings[0].values
