import time

from google import genai

from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    TOP_K
)

from rag.embeddings import (
    generate_embedding
)

from rag.vector_store import (
    search_documents
)


# =====================================================
# GEMINI CLIENT
# =====================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =====================================================
# HELPER: BUILD SOURCES
# =====================================================

def build_sources(
    metadatas
):

    sources = []

    for metadata in metadatas:

        source = {
            "source":
                metadata.get("source"),

            "page":
                metadata.get("page")
        }

        if source not in sources:

            sources.append(
                source
            )

    return sources


# =====================================================
# HELPER: BUILD RAG PROMPT
# =====================================================

def build_prompt(
    question,
    documents,
    metadatas
):

    context_parts = []

    for index, document in enumerate(
        documents
    ):

        metadata = metadatas[index]

        context_parts.append(
            f"""
Source: {metadata.get("source")}

Page: {metadata.get("page")}

Content:

{document}
"""
        )

    context = "\n\n".join(
        context_parts
    )

    prompt = f"""
You are an Enterprise AI Knowledge Assistant.

Use ONLY the information provided in the
DOCUMENT CONTEXT below.

Do not invent facts.

If the answer is not present in the
documents, say:

"I could not find this information
in the uploaded documents."

Give clear and professional answers.

DOCUMENT CONTEXT:

{context}


USER QUESTION:

{question}
"""

    return prompt


# =====================================================
# NORMAL NON-STREAMING RAG
# =====================================================

def ask_question(
    question,
    user_id
):

    # -------------------------------------------------
    # Question embedding
    # -------------------------------------------------

    query_embedding = generate_embedding(
        question
    )


    # -------------------------------------------------
    # Search ChromaDB
    # -------------------------------------------------

    results = search_documents(
        query_embedding=query_embedding,
        user_id=user_id,
        top_k=TOP_K
    )


    documents = results.get(
        "documents",
        [[]]
    )[0]


    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]


    # -------------------------------------------------
    # No documents
    # -------------------------------------------------

    if not documents:

        return {
            "answer":
                "I could not find relevant "
                "information in your uploaded "
                "documents.",

            "sources": []
        }


    # -------------------------------------------------
    # Build prompt
    # -------------------------------------------------

    prompt = build_prompt(
        question=question,
        documents=documents,
        metadatas=metadatas
    )


    # -------------------------------------------------
    # Gemini response
    # -------------------------------------------------

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )


    # -------------------------------------------------
    # Sources
    # -------------------------------------------------

    sources = build_sources(
        metadatas
    )


    return {
        "answer":
            response.text,

        "sources":
            sources
    }


# =====================================================
# STREAMING RAG
# =====================================================

def stream_question(
    question,
    user_id
):

    # -------------------------------------------------
    # Generate question embedding
    # -------------------------------------------------

    try:

        query_embedding = generate_embedding(
            question
        )

    except Exception as error:

        print(
            "Embedding error:",
            str(error)
        )

        yield {
            "type": "error",

            "message":
                "Failed to process your question. "
                "Please try again."
        }

        return


    # -------------------------------------------------
    # Search user's documents
    # -------------------------------------------------

    try:

        results = search_documents(
            query_embedding=query_embedding,
            user_id=user_id,
            top_k=TOP_K
        )

    except Exception as error:

        print(
            "Vector search error:",
            str(error)
        )

        yield {
            "type": "error",

            "message":
                "Failed to search the knowledge base."
        }

        return


    documents = results.get(
        "documents",
        [[]]
    )[0]


    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]


    # =================================================
    # NO DOCUMENTS
    # =================================================

    if not documents:

        yield {
            "type": "chunk",

            "content":
                "I could not find relevant "
                "information in your uploaded "
                "documents."
        }


        yield {
            "type": "sources",
            "sources": []
        }


        return


    # =================================================
    # BUILD PROMPT
    # =================================================

    prompt = build_prompt(
        question=question,
        documents=documents,
        metadatas=metadatas
    )


    # =================================================
    # GEMINI STREAMING WITH RETRY
    # =================================================

    max_attempts = 3

    stream_completed = False


    for attempt in range(
        1,
        max_attempts + 1
    ):

        stream_started = False


        try:

            print(
                f"Gemini streaming attempt "
                f"{attempt}/{max_attempts}"
            )


            # -----------------------------------------
            # Start Gemini streaming
            # -----------------------------------------

            response_stream = (
                client.models.generate_content_stream(
                    model=GEMINI_MODEL,
                    contents=prompt
                )
            )


            # -----------------------------------------
            # Read Gemini chunks
            # -----------------------------------------

            for chunk in response_stream:

                if chunk.text:

                    stream_started = True


                    yield {
                        "type": "chunk",
                        "content": chunk.text
                    }


            # -----------------------------------------
            # Success
            # -----------------------------------------

            stream_completed = True

            print(
                "Gemini streaming completed."
            )

            break


        except Exception as error:

            error_message = str(
                error
            )


            print(
                f"Gemini streaming error "
                f"attempt {attempt}:",
                error_message
            )


            # =========================================
            # 429 QUOTA / RATE LIMIT
            # =========================================

            is_quota_error = (

                "429" in error_message

                or

                "RESOURCE_EXHAUSTED"
                in error_message

                or

                "quota" in
                error_message.lower()
            )


            if is_quota_error:

                print(
                    "Gemini quota exhausted. "
                    "Not retrying."
                )


                # If no answer text has been sent yet,
                # send a friendly error to frontend.

                if not stream_started:

                    yield {
                        "type": "error",

                        "message":
                            "Gemini API quota has "
                            "been reached. "
                            "Please try again later."
                    }

                else:

                    yield {
                        "type": "error",

                        "message":
                            "The AI response was "
                            "interrupted because the "
                            "Gemini API quota was "
                            "reached."
                    }


                return


            # =========================================
            # 503 TEMPORARY GEMINI OVERLOAD
            # =========================================

            is_temporary_error = (

                "503" in error_message

                or

                "UNAVAILABLE"
                in error_message

                or

                "high demand"
                in error_message.lower()
            )


            if is_temporary_error:

                # -------------------------------------
                # Do NOT restart after answer started
                # -------------------------------------

                if stream_started:

                    yield {
                        "type": "error",

                        "message":
                            "The AI response was "
                            "interrupted. "
                            "Please try again."
                    }

                    return


                # -------------------------------------
                # Last retry failed
                # -------------------------------------

                if attempt == max_attempts:

                    yield {
                        "type": "error",

                        "message":
                            "Gemini is temporarily "
                            "busy. Please try again "
                            "in a few moments."
                    }

                    return


                # -------------------------------------
                # Exponential backoff
                #
                # Attempt 1 -> 2 seconds
                # Attempt 2 -> 4 seconds
                # -------------------------------------

                wait_seconds = (
                    2 ** attempt
                )


                print(
                    "Gemini temporarily unavailable. "
                    f"Retrying in {wait_seconds} "
                    "seconds..."
                )


                time.sleep(
                    wait_seconds
                )


                continue


            # =========================================
            # OTHER GEMINI ERRORS
            # =========================================

            print(
                "Unexpected Gemini error:",
                error_message
            )


            yield {
                "type": "error",

                "message":
                    "The AI service encountered "
                    "an unexpected error. "
                    "Please try again."
            }


            return


    # =================================================
    # STREAM DID NOT COMPLETE
    # =================================================

    if not stream_completed:

        yield {
            "type": "error",

            "message":
                "The AI response could not "
                "be completed."
        }

        return


    # =================================================
    # SOURCES
    # =================================================

    sources = build_sources(
        metadatas
    )


    # =================================================
    # SEND SOURCES
    # =================================================

    yield {
        "type": "sources",
        "sources": sources
    }
