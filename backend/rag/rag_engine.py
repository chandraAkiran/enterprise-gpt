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


client = genai.Client(
    api_key=GEMINI_API_KEY
)


def ask_question(
    question,
    user_id
):

    # --------------------------------------
    # 1. Convert question into embedding
    # --------------------------------------

    query_embedding = generate_embedding(
        question
    )


    # --------------------------------------
    # 2. Search only this user's documents
    # --------------------------------------

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


    # --------------------------------------
    # 3. No relevant information
    # --------------------------------------

    if not documents:

        return {

            "answer":
                "I could not find relevant "
                "information in your uploaded "
                "documents.",

            "sources": []
        }


    # --------------------------------------
    # 4. Create context
    # --------------------------------------

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


    # --------------------------------------
    # 5. Prompt
    # --------------------------------------

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


    # --------------------------------------
    # 6. Gemini
    # --------------------------------------

    response = client.models.generate_content(

        model=GEMINI_MODEL,

        contents=prompt
    )


    # --------------------------------------
    # 7. Sources
    # --------------------------------------

    sources = []


    for metadata in metadatas:

        sources.append({

            "source":
                metadata.get("source"),

            "page":
                metadata.get("page")
        })


    return {

        "answer":
            response.text,

        "sources":
            sources
    }
