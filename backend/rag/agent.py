from langchain.agents import (
    create_agent,
)

from rag.langchain_llm import (
    llm,
)

from rag.agent_tools import (
    create_document_search_tool,
)

from rag.langchain_chain import (
    retrieve_context,
)


# =====================================================
# AGENT SYSTEM PROMPT
# =====================================================

AGENT_SYSTEM_PROMPT = """
You are an Enterprise AI Knowledge Assistant.

You have access to a tool that searches the
authenticated user's uploaded enterprise documents.

When the user asks about company policies,
reports, manuals, procedures, guidelines,
or other information that may exist in their
uploaded documents, use the document search tool.

Use information returned by the tool when
answering document-related questions.

Do not invent company information.

If the information cannot be found in the
uploaded documents, clearly say so.
"""


# =====================================================
# CREATE USER-SPECIFIC AGENT
# =====================================================

def create_user_agent(
    user_id: str,
):

    # Create a document search tool that is locked
    # to the authenticated user's ID.
    document_tool = (
        create_document_search_tool(
            user_id=user_id,
        )
    )

    # Create LangChain Agent.
    agent = create_agent(
        model=llm,
        tools=[
            document_tool,
        ],
        system_prompt=(
            AGENT_SYSTEM_PROMPT
        ),
    )

    return agent


# =====================================================
# EXTRACT TEXT FROM AGENT RESPONSE
# =====================================================

def extract_answer_text(
    content,
) -> str:
    """
    Convert LangChain/Gemini structured message
    content into a plain string.
    """

    # Normal string response
    if isinstance(content, str):
        return content

    # Gemini/LangChain may return a list
    # containing structured content blocks.
    if isinstance(content, list):

        text_parts = []

        for part in content:

            # Plain string inside list
            if isinstance(part, str):

                text_parts.append(
                    part
                )

            # Dictionary content block
            elif isinstance(part, dict):

                text = part.get(
                    "text"
                )

                if text:

                    text_parts.append(
                        str(text)
                    )

            # Object content block
            else:

                text = getattr(
                    part,
                    "text",
                    None,
                )

                if text:

                    text_parts.append(
                        str(text)
                    )

        return "".join(
            text_parts
        )

    # Dictionary response
    if isinstance(content, dict):

        text = content.get(
            "text"
        )

        if text:
            return str(text)

        return str(content)

    # Object response such as:
    # {type, text, extras}
    text = getattr(
        content,
        "text",
        None,
    )

    if text:
        return str(text)

    # Final fallback
    return str(content)


# =====================================================
# EXECUTE AGENT
# =====================================================

def ask_agent(
    question: str,
    user_id: str,
):

    # Create an Agent specifically for
    # the authenticated user.
    user_agent = create_user_agent(
        user_id=user_id,
    )

    # Send the user's question to the Agent.
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

    # Get all messages generated during
    # Agent execution.
    messages = result.get(
        "messages",
        []
    )

    if not messages:

        return {
            "answer":
                "I could not generate an answer."
        }

    # Final message contains the
    # Agent's final response.
    final_message = messages[-1]

    content = getattr(
        final_message,
        "content",
        "",
    )

    # Convert structured Gemini/LangChain
    # content into plain text.
    answer = extract_answer_text(
        content
    )

    if not answer.strip():

        answer = (
            "I could not generate an answer."
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
):

    # Create an Agent locked to the
    # authenticated user.
    user_agent = create_user_agent(
        user_id=user_id,
    )

    # Retrieve metadata separately so the
    # frontend can display clean sources.
    retrieval = retrieve_context(
        question=question,
        user_id=user_id,
    )

    sources = retrieval.get(
        "sources",
        [],
    )

    try:

        # Stream Agent execution.
        for event in user_agent.stream(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": question,
                    }
                ]
            },
            stream_mode="messages",
        ):

            # LangChain may return:
            # (message_chunk, metadata)
            if (
                isinstance(event, tuple)
                and len(event) >= 1
            ):

                message = event[0]

            else:

                message = event

            # -----------------------------------------
            # Do not expose raw tool output
            # -----------------------------------------

            message_type = getattr(
                message,
                "type",
                "",
            )

            if message_type == "tool":
                continue

            # -----------------------------------------
            # Extract streamed text
            # -----------------------------------------

            content = getattr(
                message,
                "content",
                "",
            )

            if not content:
                continue

            text = extract_answer_text(
                content
            )

            if text:

                yield {
                    "type": "chunk",
                    "content": text,
                }

        # ---------------------------------------------
        # Send structured sources after answer
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
            error_message,
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
                    "Please try again later.",
            }

            return

        # ---------------------------------------------
        # Gemini temporary unavailable error
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
                    "Please try again in a few moments.",
            }

            return

        # ---------------------------------------------
        # Generic error
        # ---------------------------------------------

        yield {
            "type": "error",
            "message":
                "The Agent encountered an "
                "unexpected error.",
        }
