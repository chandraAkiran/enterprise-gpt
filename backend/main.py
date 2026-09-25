import os
import uuid
import json

from pathlib import Path

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

from rag.langchain_chain import (
    stream_with_langchain,
)


# =====================================================
# FASTAPI APP
# =====================================================

app = FastAPI(
    title="Enterprise GPT API",
    description=(
        "Enterprise AI Knowledge Assistant "
        "using Gemini, ChromaDB and Supabase"
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

DOCUMENT_DIR = "documents"

os.makedirs(
    DOCUMENT_DIR,
    exist_ok=True,
)


# =====================================================
# REQUEST MODELS
# =====================================================

class ChatRequest(BaseModel):
    question: str


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

    user_id = str(
        user.id
    )

    # -------------------------------------------------
    # Validate file
    # -------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="File name is missing",
        )

    if not file.filename.lower().endswith(
        ".pdf"
    ):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported",
        )

    # -------------------------------------------------
    # Create document ID
    # -------------------------------------------------

    document_id = str(
        uuid.uuid4()
    )

    # -------------------------------------------------
    # Read uploaded PDF
    # -------------------------------------------------

    contents = await file.read()

    if not contents:

        raise HTTPException(
            status_code=400,
            detail="Uploaded PDF is empty",
        )

    # -------------------------------------------------
    # Supabase Storage path
    # -------------------------------------------------

    storage_path = (
        f"{user_id}/"
        f"{document_id}_{file.filename}"
    )

    # -------------------------------------------------
    # Temporary local PDF path
    # -------------------------------------------------

    temp_file_path = os.path.join(
        DOCUMENT_DIR,
        f"{document_id}_{file.filename}",
    )

    try:

        # ---------------------------------------------
        # Upload original PDF to Supabase Storage
        # ---------------------------------------------

        supabase.storage.from_(
            "documents"
        ).upload(
            path=storage_path,
            file=contents,
            file_options={
                "content-type":
                    "application/pdf"
            },
        )

        # ---------------------------------------------
        # Save temporary local copy
        # ---------------------------------------------

        with open(
            temp_file_path,
            "wb",
        ) as temp_file:

            temp_file.write(
                contents
            )

        # ---------------------------------------------
        # Extract PDF pages
        # ---------------------------------------------

        pages = extract_pdf_pages(
            Path(temp_file_path)
        )

        for page in pages:
            page["source"] = file.filename

        if not pages:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No text could be extracted "
                    "from the PDF"
                ),
            )

        # ---------------------------------------------
        # Create chunks
        # ---------------------------------------------

        chunks = create_chunks(
            pages
        )

        if not chunks:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No text chunks could be "
                    "created from the PDF"
                ),
            )

        # ---------------------------------------------
        # Generate embedding for every chunk
        # ---------------------------------------------

        embeddings = []

        for chunk in chunks:

            embedding = generate_embedding(
                chunk["text"]
            )

            embeddings.append(
                embedding
            )

        # ---------------------------------------------
        # Store chunks + vectors in ChromaDB
        # ---------------------------------------------

        stored_chunks = add_documents(
            chunks=chunks,
            embeddings=embeddings,
            user_id=user_id,
            document_id=document_id,
        )

        # ---------------------------------------------
        # Save document record in Supabase
        # ---------------------------------------------

        database_result = (
    supabase
    .table("documents")
    .insert(
        {
            "id":
                document_id,

            "user_id":
                user_id,

            "file_name":
                file.filename,

            "file_path":
                storage_path,

            "page_count":
                len(pages),

            "chunk_count":
                stored_chunks,

            "status":
                "ready",
        }
    )
    .execute()
)

        # ---------------------------------------------
        # Success
        # ---------------------------------------------

        return {
            "message":
                "Document uploaded successfully",

            "document_id":
                document_id,

            "file_name":
                file.filename,

            "chunks":
                stored_chunks,

            "document":
                database_result.data,
        }

    except HTTPException:

        raise

    except Exception as error:

        print(
            "Upload error:",
            str(error),
        )

        # ---------------------------------------------
        # Clean up Storage if processing failed
        # ---------------------------------------------

        try:

            supabase.storage.from_(
                "documents"
            ).remove([
                storage_path
            ])

        except Exception as cleanup_error:

            print(
                "Storage cleanup error:",
                str(cleanup_error),
            )

        raise HTTPException(
            status_code=500,
            detail="Failed to upload document",
        )

    finally:

        # ---------------------------------------------
        # Remove temporary local PDF
        # ---------------------------------------------

        if os.path.exists(
            temp_file_path
        ):

            try:

                os.remove(
                    temp_file_path
                )

            except Exception as cleanup_error:

                print(
                    "Temporary file cleanup error:",
                    str(cleanup_error),
                )


# =====================================================
# NORMAL CHAT
# =====================================================

@app.post("/chat")
def chat(
    request: ChatRequest,
    user=Depends(get_current_user),
):

    user_id = str(
        user.id
    )

    if not request.question.strip():

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty",
        )

    try:

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
# STREAMING CHAT - LANGCHAIN
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
    # Streaming generator
    # -------------------------------------------------

    def generate():

        try:

            # =========================================
            # LANGCHAIN STREAM
            # =========================================

            response_stream = (
                stream_with_langchain(
                    question=request.question,
                    user_id=user_id,
                )
            )


            # =========================================
            # SEND NDJSON EVENTS
            # =========================================

            for event in response_stream:

                json_event = json.dumps(
                    event,
                    ensure_ascii=False,
                )

                yield (
                    json_event + "\n"
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
                    error_event
                )
                + "\n"
            )


    # -------------------------------------------------
    # Return streaming response
    # -------------------------------------------------

    return StreamingResponse(
        generate(),
        media_type=(
            "application/x-ndjson"
        ),
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
        # Delete vectors from ChromaDB
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
    admin=Depends(get_current_admin),
):

    try:

        # ---------------------------------------------
        # 1. Find document
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
        # 2. Get document owner
        # ---------------------------------------------

        document_owner_id = str(
            document["user_id"]
        )

        # ---------------------------------------------
        # 3. Delete vectors
        # ---------------------------------------------

        delete_document(
            user_id=document_owner_id,
            document_id=document_id,
        )

        # ---------------------------------------------
        # 4. Delete PDF from Storage
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
        # 5. Delete database record
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
        # 6. Success
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
