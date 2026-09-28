from langchain.agents import create_agent

from llm.provider import get_llm

from rag.agent_tools import (
    create_document_search_tool
)

from rag.langchain_chain import (
    retrieve_context
)


# =====================================================
# AGENT SYSTEM PROMPT
# =====================================================

AGENT_SYSTEM_PROMPT = """
You are an Enterprise AI Knowledge Assistant.

Your job is to help users answer questions using
their enterprise documents.

When a question is related to company policies,
reports, manuals, procedures, guidelines, or other
uploaded enterprise documents, use the
search_enterprise_documents tool.

Use information returned by the tool to answer
the user's question.

Do not invent company information.

If the required information cannot be found in
the uploaded documents, clearly tell the user.

Give clear, professional, and concise answers.
"""


# =====================================================
# CREATE USER-SPECIFIC AGENT
# =====================================================

def create_user_agent(
    user_id: str,
    provider: str = "gemini",
):

    # ---------------------------------------------
    # Create secure user-specific document tool
    # ---------------------------------------------

    document_search_tool = (
        create_document_search_tool(
            user_id=user_id
        )
    )

    # ---------------------------------------------
    # Select LLM provider
    # ---------------------------------------------

    selected_llm = get_llm(
        provider
    )

    # ---------------------------------------------
    # Create LangChain Agent
    # ---------------------------------------------

    user_agent = create_agent(
        model=selected_llm,
        tools=[
            document_search_tool
        ],
        system_prompt=AGENT_SYSTEM_PROMPT,
    )

    return user_agent


# =====================================================
# EXTRACT TEXT FROM AGENT MESSAGE
# =====================================================

def extract_answer_text(
    content
):

    # ---------------------------------------------
    # Normal string response
    # ---------------------------------------------

    if isinstance(
        content,
        str
    ):

        return content


    # ---------------------------------------------
    # Structured LangChain / Gemini / OpenAI response
    # ---------------------------------------------

    if isinstance(
        content,
        list
    ):

        text_parts = []

        for item in content:

            if isinstance(
                item,
                str
            ):

                text_parts.append(
                    item
                )

            elif isinstance(
                item,
                dict
            ):

                text = item.get(
                    "text"
                )

                if text:

                    text_parts.append(
                        str(text)
                    )

            else:

                text = getattr(
                    item,
                    "text",
                    None
                )

                if text:

                    text_parts.append(
                        str(text)
                    )

        return "".join(
            text_parts
        )


    # ---------------------------------------------
    # Dictionary response
    # ---------------------------------------------

    if isinstance(
        content,
        dict
    ):

        text = content.get(
            "text"
        )

        if text:

            return str(
                text
            )


    # ---------------------------------------------
    # Object containing text attribute
    # ---------------------------------------------

    text = getattr(
        content,
        "text",
        None
    )

    if text:

        return str(
            text
        )


    return ""


# =====================================================
# ASK AGENT
# =====================================================

def ask_agent(
    question: str,
    user_id: str,
    provider: str = "gemini",
):

    # ---------------------------------------------
    # Create authenticated user's agent
    # using selected LLM provider
    # ---------------------------------------------

    user_agent = create_user_agent(
        user_id=user_id,
        provider=provider,
    )

    # ---------------------------------------------
    # Run Agent
    # ---------------------------------------------

    result = user_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": question,
                }
            ]
        }
    )

    # ---------------------------------------------
    # Extract final Agent answer
    # ---------------------------------------------

    messages = result.get(
        "messages",
        []
    )

    if not messages:

        return {
            "answer":
                "The Agent did not return "
                "a response."
        }

    final_message = messages[-1]

    answer = extract_answer_text(
        final_message.content
    )

    return {
        "answer": answer
    }


# =====================================================
# STREAM AGENT
# =====================================================

def stream_agent(
    question: str,
    user_id: str,
    provider: str = "gemini",
):

    try:

        # ---------------------------------------------
        # Create authenticated user's agent
        # using selected LLM provider
        # ---------------------------------------------

        user_agent = create_user_agent(
            user_id=user_id,
            provider=provider,
        )


        # ---------------------------------------------
        # Retrieve source metadata
        # ---------------------------------------------

        retrieval = retrieve_context(
            question=question,
            user_id=user_id,
        )

        sources = retrieval.get(
            "sources",
            [],
        )


        # ---------------------------------------------
        # Stream Agent response
        # ---------------------------------------------

        response_stream = user_agent.stream(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": question,
                    }
                ]
            },
            stream_mode="messages",
        )


        for event in response_stream:

            # -----------------------------------------
            # LangChain may return:
            #
            # (message, metadata)
            # -----------------------------------------

            if isinstance(
                event,
                tuple
            ):

                message = event[0]

            else:

                message = event


            # -----------------------------------------
            # Skip tool output
            # -----------------------------------------

            message_type = getattr(
                message,
                "type",
                None
            )

            if message_type == "tool":

                continue


            # -----------------------------------------
            # Extract streamed text
            # -----------------------------------------

            content = getattr(
                message,
                "content",
                None
            )

            if not content:

                continue


            text = extract_answer_text(
                content
            )

            if not text:

                continue


            yield {
                "type": "chunk",
                "content": text,
            }


        # ---------------------------------------------
        # Send sources after answer
        # ---------------------------------------------

        yield {
            "type": "sources",
            "sources": sources,
        }


    except Exception as error:

        error_message = str(
            error
        )

        print(
            "Agent streaming error:",
            error_message
        )


        # ---------------------------------------------
        # API quota / credit error
        # Gemini or OpenAI
        # ---------------------------------------------

        if (
            "429" in error_message
            or
            "RESOURCE_EXHAUSTED"
            in error_message
            or
            "quota" in error_message.lower()
            or
            "insufficient_quota"
            in error_message.lower()
            or
            "credit_balance_exhausted"
            in error_message.lower()
        ):

            yield {
                "type": "error",
                "message":
                    "The selected AI provider "
                    "has reached its API quota "
                    "or credit limit.",
            }

            return


        # ---------------------------------------------
        # Temporary provider error
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
                    "The selected AI provider "
                    "is temporarily unavailable. "
                    "Please try again shortly.",
            }

            return


        # ---------------------------------------------
        # Other error
        # ---------------------------------------------

        yield {
            "type": "error",
            "message":
                "The AI Agent encountered "
                "an unexpected error. "
                "Please try again.",
        }
