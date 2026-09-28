from langchain_core.tools import tool

from rag.langchain_chain import (
    retrieve_context,
)


# =====================================================
# CREATE USER-SPECIFIC DOCUMENT SEARCH TOOL
# =====================================================

def create_document_search_tool(
    user_id: str,
):

    @tool
    def search_enterprise_documents(
        question: str,
    ) -> str:
        """
        Search the authenticated user's uploaded
        enterprise documents.

        Use this tool for questions about company
        policies, reports, manuals, procedures,
        guidelines, or other uploaded documents.
        """

        retrieval = retrieve_context(
            question=question,
            user_id=user_id,
        )

        if not retrieval[
            "documents_found"
        ]:
            return (
                "No relevant information was found "
                "in the uploaded documents."
            )

        return retrieval["context"]

    return search_enterprise_documents
