from langchain_core.prompts import (
    ChatPromptTemplate
)

from langchain_core.output_parsers import (
    StrOutputParser
)

from rag.langchain_llm import (
    llm
)

from rag.embeddings import (
    generate_embedding
)

from rag.vector_store import (
    search_documents
)

from config import (
    TOP_K
)


# =====================================================
# ENTERPRISE RAG PROMPT
# =====================================================

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
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
"""
        ),
        (
            "human",
            "{question}"
        )
    ]
)


# =====================================================
# LANGCHAIN RAG CHAIN
# =====================================================

rag_chain = (
    prompt
    | llm
    | StrOutputParser()
)


# =====================================================
# BUILD DOCUMENT CONTEXT
# =====================================================

def build_context(
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

    return "\n\n".join(
        context_parts
    )


# =====================================================
# BUILD SOURCES
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
# RETRIEVE USER DOCUMENTS
# =====================================================

def retrieve_context(
    question,
    user_id
):

    # Generate embedding for the question

    query_embedding = generate_embedding(
        question
    )


    # Search user's ChromaDB documents

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


    # No documents found

    if not documents:

        return {
            "context": "",
            "sources": [],
            "documents_found": False
        }


    # Build context

    context = build_context(
        documents=documents,
        metadatas=metadatas
    )


    # Build sources

    sources = build_sources(
        metadatas
    )


    return {
        "context": context,
        "sources": sources,
        "documents_found": True
    }


# =====================================================
# ASK QUESTION USING LANGCHAIN
# =====================================================

def ask_with_langchain(
    question,
    user_id
):

    retrieval = retrieve_context(
        question=question,
        user_id=user_id
    )


    # No relevant documents

    if not retrieval[
        "documents_found"
    ]:

        return {
            "answer":
                "I could not find relevant "
                "information in your uploaded "
                "documents.",

            "sources": []
        }


    # Run LangChain pipeline

    answer = rag_chain.invoke(
        {
            "context":
                retrieval["context"],

            "question":
                question
        }
    )


    return {
        "answer":
            answer,

        "sources":
            retrieval["sources"]
    }

# =====================================================
# STREAM ANSWER USING LANGCHAIN
# =====================================================

def stream_with_langchain(
    question,
    user_id
):

    try:

        # ---------------------------------------------
        # Retrieve documents
        # ---------------------------------------------

        retrieval = retrieve_context(
            question=question,
            user_id=user_id
        )


        # ---------------------------------------------
        # No documents found
        # ---------------------------------------------

        if not retrieval[
            "documents_found"
        ]:

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


        # ---------------------------------------------
        # Stream answer from LangChain
        # ---------------------------------------------

        for chunk in rag_chain.stream(
            {
                "context":
                    retrieval["context"],

                "question":
                    question
            }
        ):

            if chunk:

                yield {
                    "type": "chunk",
                    "content": chunk
                }


        # ---------------------------------------------
        # Send sources after answer
        # ---------------------------------------------

        yield {
            "type": "sources",
            "sources":
                retrieval["sources"]
        }


    except Exception as error:

        error_message = str(error)

        print(
            "LangChain streaming error:",
            error_message
        )


        # ---------------------------------------------
        # Gemini quota error
        # ---------------------------------------------

        if (
            "429" in error_message
            or
            "RESOURCE_EXHAUSTED"
            in error_message
            or
            "quota"
            in error_message.lower()
        ):

            yield {
                "type": "error",
                "message":
                    "Gemini API quota has "
                    "been reached. "
                    "Please try again later."
            }

            return


        # ---------------------------------------------
        # Gemini temporary error
        # ---------------------------------------------

        if (
            "503" in error_message
            or
            "UNAVAILABLE"
            in error_message
            or
            "high demand"
            in error_message.lower()
        ):

            yield {
                "type": "error",
                "message":
                    "Gemini is temporarily busy. "
                    "Please try again in a few moments."
            }

            return


        # ---------------------------------------------
        # Other error
        # ---------------------------------------------

        yield {
            "type": "error",
            "message":
                "The AI service encountered "
                "an unexpected error. "
                "Please try again."
        }
