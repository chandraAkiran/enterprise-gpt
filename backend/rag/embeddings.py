import time

from google import genai
from google.genai import types

from config import (
    GEMINI_API_KEY,
    EMBEDDING_MODEL
)


client = genai.Client(
    api_key=GEMINI_API_KEY
)


def generate_embedding(
    text,
    max_retries=3
):

    for attempt in range(
        max_retries
    ):

        try:

            result = (
                client.models.embed_content(
                    model=EMBEDDING_MODEL,
                    contents=text,
                    config=(
                        types.EmbedContentConfig(
                            output_dimensionality=768
                        )
                    )
                )
            )

            return (
                result
                .embeddings[0]
                .values
            )

        except Exception as error:

            error_message = str(
                error
            )

            print(
                f"Embedding attempt "
                f"{attempt + 1} failed:",
                error_message
            )

            # Gemini temporary outage
            if (
                "503" in error_message
                or
                "UNAVAILABLE"
                in error_message
                or
                "service is currently unavailable"
                in error_message.lower()
            ):

                if attempt < (
                    max_retries - 1
                ):

                    wait_time = (
                        2 ** attempt
                    )

                    print(
                        f"Retrying embedding "
                        f"in {wait_time} seconds..."
                    )

                    time.sleep(
                        wait_time
                    )

                    continue

            # Do not retry quota errors
            if (
                "429" in error_message
                or
                "RESOURCE_EXHAUSTED"
                in error_message
                or
                "quota" in
                error_message.lower()
            ):

                raise RuntimeError(
                    "Gemini embedding quota "
                    "has been reached."
                )

            raise

    raise RuntimeError(
        "Failed to generate embedding "
        "after multiple attempts."
    )
