import os
import uuid
import json

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Depends,
    HTTPException,
)

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from fastapi.responses import (
    StreamingResponse,
)

from pydantic import BaseModel


# =====================================================
# PROJECT IMPORTS
# =====================================================

from auth import (
    supabase,
    get_current_user,
    get_current_admin,
)

from ingestion.pdf_loader import (
    extract_pdf_pages,
)

from ingestion.chunker import (
    create_chunks,
)

from rag.embeddings import (
    generate_embedding,
)

from rag.vector_store import (
    add_documents,
    delete_document,
)

from rag.rag_engine import (
    ask_question,
    stream_question,
)

from rag.agent import (
    ask_agent,
    stream_agent,
)


# =====================================================
# FASTAPI APP
# =====================================================

app = FastAPI(
    title="Enterprise GPT API",
    description=(
        "Enterprise AI Knowledge Assistant "
        "using RAG, LangChain Agents, "
        "multiple LLMs, ChromaDB and Supabase"
    ),
    version="1.0.0",
)


# =====================================================
# CORS
# =====================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://enterprise-gpt-self.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# DOCUMENT DIRECTORY
# =====================================================

from pathlib import Path

DOCUMENT_DIR = Path("documents")
DOCUMENT_DIR.mkdir(parents=True, exist_ok=True)


# =====================================================
# REQUEST MODELS
# =====================================================

class ChatRequest(BaseModel):
    question: str
    provider: str = "gemini"


# =====================================================
# SUPPORTED LLM PROVIDERS
# =====================================================

SUPPORTED_PROVIDERS = {
    "gemini",
    "openai",
}


def validate_provider(
    provider: str,
):

    provider = (
        provider
        .lower()
        .strip()
    )

    if provider not in SUPPORTED_PROVIDERS:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported AI provider. "
                "Use 'gemini' or 'openai'."
            ),
        )

    return provider


# =====================================================
# ROOT
# =====================================================

@app.get("/")
def root():

    return {
        "message":
            "Enterprise GPT API is running"
    }


# =====================================================
# HEALTH CHECK
# =====================================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy"
    }


# =====================================================
# UPLOAD DOCUMENT
# =====================================================

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is missing")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    user_id = str(user.id)
    document_id = str(uuid.uuid4())
    contents = await file.read()

    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty")

    storage_path = f"{user_id}/{document_id}_{file.filename}"
    safe_filename = f"{user_id}_{document_id}_{file.filename}"
    file_path = DOCUMENT_DIR / safe_filename

    storage_uploaded = False
    db_created = False

    try:
        with open(file_path, "wb") as output_file:
            output_file.write(contents)

        supabase.storage.from_("documents").upload(
            path=storage_path,
            file=contents,
            file_options={"content-type": "application/pdf"},
        )
        storage_uploaded = True

        supabase.table("documents").insert({
            "id": document_id,
            "user_id": user_id,
            "file_name": file.filename,
            "file_path": storage_path,
            "status": "processing",
        }).execute()
        db_created = True

        pages = extract_pdf_pages(file_path)
        chunks = create_chunks(pages)

        if not chunks:
            raise ValueError("No text could be extracted from the PDF")

        embeddings = []
        for chunk in chunks:
            embeddings.append(generate_embedding(chunk["text"]))

        chunk_count = add_documents(
            chunks=chunks,
            embeddings=embeddings,
            user_id=user_id,
            document_id=document_id,
        )

        supabase.table("documents").update({
            "page_count": len(pages),
            "chunk_count": chunk_count,
            "status": "ready",
        }).eq("id", document_id).eq("user_id", user_id).execute()

        return {
            "message": "Document uploaded successfully",
            "document_id": document_id,
            "file_name": file.filename,
            "pages": len(pages),
            "chunks": chunk_count,
        }

    except HTTPException:
        raise

    except Exception as error:
        print("Upload error:", str(error))

        if db_created:
            try:
                supabase.table("documents").update({
                    "status": "failed"
                }).eq("id", document_id).eq("user_id", user_id).execute()
            except Exception as db_error:
                print("Database cleanup error:", str(db_error))

        if storage_uploaded:
            try:
                supabase.storage.from_("documents").remove([storage_path])
            except Exception as storage_error:
                print("Storage cleanup error:", str(storage_error))

        raise HTTPException(status_code=500, detail=str(error))

    finally:
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as cleanup_error:
                print("Temporary file cleanup error:", str(cleanup_error))


# =====================================================
# NORMAL RAG CHAT
# =====================================================

@app.post("/chat")
def chat(
    request: ChatRequest,
    user=Depends(get_current_user),
):

    user_id = str(
        user.id
    )


    # -------------------------------------------------
    # Validate question
    # -------------------------------------------------

    if not request.question.strip():

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty",
        )


    try:

        # ---------------------------------------------
        # Ask RAG engine
        # ---------------------------------------------

        result = ask_question(
            question=request.question,
            user_id=user_id,
        )


        return result


    except HTTPException:

        raise


    except Exception as error:

        print(
            "Chat error:",
            str(error),
        )


        raise HTTPException(
            status_code=500,
            detail="Failed to generate answer",
        )


# =====================================================
# STREAMING RAG CHAT
# =====================================================

@app.post("/chat/stream")
def chat_stream(
    request: ChatRequest,
    user=Depends(get_current_user),
):

    user_id = str(
        user.id
    )


    # -------------------------------------------------
    # Validate question
    # -------------------------------------------------

    if not request.question.strip():

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty",
        )


    # -------------------------------------------------
    # Convert RAG events to NDJSON
    # -------------------------------------------------

    def generate():

        try:

            response_stream = stream_question(
                question=request.question,
                user_id=user_id,
            )


            for event in response_stream:

                json_event = json.dumps(
                    event,
                    ensure_ascii=False,
                )

                yield (
                    json_event +
                    "\n"
                )


        except Exception as error:

            print(
                "Streaming error:",
                str(error),
            )


            error_event = {
                "type": "error",
                "message":
                    "Failed to generate answer",
            }


            yield (
                json.dumps(
                    error_event,
                    ensure_ascii=False,
                )
                +
                "\n"
            )


    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control":
                "no-cache",

            "X-Accel-Buffering":
                "no",
        },
    )


# =====================================================
# AGENT CHAT
# =====================================================

@app.post("/agent/chat")
def agent_chat(
    request: ChatRequest,
    user=Depends(get_current_user),
):

    user_id = str(
        user.id
    )


    # -------------------------------------------------
    # Validate question
    # -------------------------------------------------

    if not request.question.strip():

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty",
        )


    # -------------------------------------------------
    # Validate LLM provider
    # -------------------------------------------------

    provider = validate_provider(
        request.provider
    )


    try:

        # ---------------------------------------------
        # Ask Agent
        # ---------------------------------------------

        result = ask_agent(
            question=request.question,
            user_id=user_id,
            provider=provider,
        )


        return result


    except HTTPException:

        raise


    except Exception as error:

        print(
            "Agent chat error:",
            str(error),
        )


        error_message = str(
            error
        )


        # ---------------------------------------------
        # API quota / credit error
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

            raise HTTPException(
                status_code=429,
                detail=(
                    "The selected AI provider "
                    "has reached its API quota "
                    "or credit limit."
                ),
            )


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

            raise HTTPException(
                status_code=503,
                detail=(
                    "The selected AI provider "
                    "is temporarily unavailable."
                ),
            )


        # ---------------------------------------------
        # Other error
        # ---------------------------------------------

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to generate "
                "agent response"
            ),
        )


# =====================================================
# AGENT STREAMING CHAT
# =====================================================

@app.post("/agent/chat/stream")
def agent_chat_stream(
    request: ChatRequest,
    user=Depends(get_current_user),
):

    user_id = str(
        user.id
    )


    # -------------------------------------------------
    # Validate question
    # -------------------------------------------------

    if not request.question.strip():

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty",
        )


    # -------------------------------------------------
    # Validate LLM provider
    # -------------------------------------------------

    provider = validate_provider(
        request.provider
    )


    # -------------------------------------------------
    # Generate NDJSON stream
    # -------------------------------------------------

    def generate():

        try:

            response_stream = stream_agent(
                question=request.question,
                user_id=user_id,
                provider=provider,
            )


            for event in response_stream:

                json_event = json.dumps(
                    event,
                    ensure_ascii=False,
                )

                yield (
                    json_event +
                    "\n"
                )


        except Exception as error:

            print(
                "Agent streaming endpoint error:",
                str(error),
            )


            error_event = {
                "type": "error",
                "message":
                    "Failed to generate "
                    "Agent response",
            }


            yield (
                json.dumps(
                    error_event,
                    ensure_ascii=False,
                )
                +
                "\n"
            )


    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control":
                "no-cache",

            "X-Accel-Buffering":
                "no",
        },
    )


# =====================================================
# GET USER DOCUMENTS
# =====================================================

@app.get("/documents")
def get_documents(
    user=Depends(get_current_user),
):

    user_id = str(
        user.id
    )


    try:

        result = (
            supabase
            .table("documents")
            .select("*")
            .eq(
                "user_id",
                user_id
            )
            .order(
                "created_at",
                desc=True
            )
            .execute()
        )


        return {
            "documents":
                result.data or []
        }


    except Exception as error:

        print(
            "Get documents error:",
            str(error),
        )


        raise HTTPException(
            status_code=500,
            detail="Failed to load documents",
        )


# =====================================================
# DELETE USER DOCUMENT
# =====================================================

@app.delete("/documents/{document_id}")
def delete_user_document(
    document_id: str,
    user=Depends(get_current_user),
):

    user_id = str(
        user.id
    )


    try:

        # ---------------------------------------------
        # Find document belonging to current user
        # ---------------------------------------------

        result = (
            supabase
            .table("documents")
            .select("*")
            .eq(
                "id",
                document_id
            )
            .eq(
                "user_id",
                user_id
            )
            .execute()
        )


        documents = (
            result.data or []
        )


        if not documents:

            raise HTTPException(
                status_code=404,
                detail="Document not found",
            )


        document = documents[0]


        # ---------------------------------------------
        # Delete vectors
        # ---------------------------------------------

        delete_document(
            user_id=user_id,
            document_id=document_id,
        )


        # ---------------------------------------------
        # Delete PDF from Supabase Storage
        # ---------------------------------------------

        storage_path = document.get(
            "file_path"
        )


        if storage_path:

            supabase.storage.from_(
                "documents"
            ).remove([
                storage_path
            ])


        # ---------------------------------------------
        # Delete database record
        # ---------------------------------------------

        (
            supabase
            .table("documents")
            .delete()
            .eq(
                "id",
                document_id
            )
            .eq(
                "user_id",
                user_id
            )
            .execute()
        )


        return {
            "message":
                "Document deleted successfully"
        }


    except HTTPException:

        raise


    except Exception as error:

        print(
            "Delete document error:",
            str(error),
        )


        raise HTTPException(
            status_code=500,
            detail="Failed to delete document",
        )


# =====================================================
# DASHBOARD
# =====================================================

@app.get("/dashboard")
def dashboard(
    user=Depends(get_current_user),
):

    user_id = str(
        user.id
    )


    try:

        # ---------------------------------------------
        # User documents
        # ---------------------------------------------

        documents_result = (
            supabase
            .table("documents")
            .select(
                "id",
                count="exact"
            )
            .eq(
                "user_id",
                user_id
            )
            .execute()
        )


        # ---------------------------------------------
        # User chat sessions
        # ---------------------------------------------

        sessions_result = (
            supabase
            .table("chat_sessions")
            .select(
                "id",
                count="exact"
            )
            .eq(
                "user_id",
                user_id
            )
            .execute()
        )


        # ---------------------------------------------
        # User chat messages
        # ---------------------------------------------

        messages_result = (
            supabase
            .table("chat_messages")
            .select(
                "id",
                count="exact"
            )
            .eq(
                "user_id",
                user_id
            )
            .execute()
        )


        return {
            "documents":
                documents_result.count or 0,

            "chat_sessions":
                sessions_result.count or 0,

            "chat_messages":
                messages_result.count or 0,
        }


    except Exception as error:

        print(
            "Dashboard error:",
            str(error),
        )


        raise HTTPException(
            status_code=500,
            detail="Failed to load dashboard",
        )


# =====================================================
# ADMIN - GET ALL DOCUMENTS
# =====================================================

@app.get("/admin/documents")
def admin_get_documents(
    admin=Depends(
        get_current_admin
    ),
):

    try:

        result = (
            supabase
            .table("documents")
            .select("*")
            .order(
                "created_at",
                desc=True
            )
            .execute()
        )


        return {
            "documents":
                result.data or []
        }


    except Exception as error:

        print(
            "Admin get documents error:",
            str(error),
        )


        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to load "
                "admin documents"
            ),
        )


# =====================================================
# ADMIN - DELETE ANY USER DOCUMENT
# =====================================================

@app.delete("/admin/documents/{document_id}")
def admin_delete_document(
    document_id: str,
    admin=Depends(
        get_current_admin
    ),
):

    try:

        # ---------------------------------------------
        # Find document
        # ---------------------------------------------

        result = (
            supabase
            .table("documents")
            .select("*")
            .eq(
                "id",
                document_id
            )
            .execute()
        )


        documents = (
            result.data or []
        )


        if not documents:

            raise HTTPException(
                status_code=404,
                detail="Document not found",
            )


        document = documents[0]


        # ---------------------------------------------
        # Get document owner
        # ---------------------------------------------

        document_owner_id = str(
            document["user_id"]
        )


        # ---------------------------------------------
        # Delete vectors from ChromaDB
        # ---------------------------------------------

        delete_document(
            user_id=document_owner_id,
            document_id=document_id,
        )


        # ---------------------------------------------
        # Delete PDF from Supabase Storage
        # ---------------------------------------------

        storage_path = document.get(
            "file_path"
        )


        if storage_path:

            supabase.storage.from_(
                "documents"
            ).remove([
                storage_path
            ])


        # ---------------------------------------------
        # Delete database record
        # ---------------------------------------------

        (
            supabase
            .table("documents")
            .delete()
            .eq(
                "id",
                document_id
            )
            .execute()
        )


        # ---------------------------------------------
        # Success
        # ---------------------------------------------

        return {
            "message":
                "Document deleted successfully by admin"
        }


    except HTTPException:

        raise


    except Exception as error:

        print(
            "Admin delete document error:",
            str(error),
        )


        raise HTTPException(
            status_code=500,
            detail="Failed to delete document",
        )
    
