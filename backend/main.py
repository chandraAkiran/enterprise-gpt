import uuid

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Depends,
    HTTPException,
)

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from auth import (
    get_current_user,
    get_current_admin,
    supabase,
)

from config import DOCUMENT_DIR

from ingestion.pdf_loader import extract_pdf_pages
from ingestion.chunker import create_chunks

from rag.embeddings import generate_embedding

from rag.vector_store import (
    add_documents,
    delete_document,
)

from rag.rag_engine import ask_question


# =====================================================
# APP
# =====================================================

app = FastAPI(
    title="Enterprise GPT API",
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
# REQUEST MODELS
# =====================================================

class ChatRequest(BaseModel):
    question: str


# =====================================================
# HOME
# =====================================================

@app.get("/")
def home():
    return {
        "message": "Enterprise GPT API is running",
        "status": "success",
    }


# =====================================================
# UPLOAD PDF
# =====================================================

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    # -------------------------------------------------
    # Validate filename
    # -------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is missing",
        )

    # -------------------------------------------------
    # Validate PDF
    # -------------------------------------------------

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported",
        )

    # -------------------------------------------------
    # User ID
    # -------------------------------------------------

    user_id = str(user.id)

    # -------------------------------------------------
    # Generate document ID
    # -------------------------------------------------

    document_id = str(uuid.uuid4())

    # -------------------------------------------------
    # Temporary local filename
    # -------------------------------------------------

    safe_filename = (
        f"{user_id}_"
        f"{document_id}_"
        f"{file.filename}"
    )

    file_path = DOCUMENT_DIR / safe_filename

    # -------------------------------------------------
    # Read uploaded PDF
    # -------------------------------------------------

    contents = await file.read()

    # -------------------------------------------------
    # Save temporary local PDF
    # -------------------------------------------------

    with open(file_path, "wb") as output_file:
        output_file.write(contents)

    # -------------------------------------------------
    # Supabase Storage path
    # -------------------------------------------------

    storage_path = (
        f"{user_id}/"
        f"{document_id}_{file.filename}"
    )

    storage_uploaded = False
    database_record_created = False

    try:
        # -------------------------------------------------
        # Upload permanent PDF to Supabase Storage
        # -------------------------------------------------

        supabase.storage.from_("documents").upload(
            path=storage_path,
            file=contents,
            file_options={
                "content-type": "application/pdf"
            },
        )

        storage_uploaded = True

        # -------------------------------------------------
        # Create database record
        # -------------------------------------------------

        supabase.table("documents").insert({
            "id": document_id,
            "user_id": user_id,
            "file_name": file.filename,
            "file_path": storage_path,
            "status": "processing",
        }).execute()

        database_record_created = True

        # -------------------------------------------------
        # Extract PDF pages
        # -------------------------------------------------

        pages = extract_pdf_pages(file_path)

        # -------------------------------------------------
        # Create chunks
        # -------------------------------------------------

        chunks = create_chunks(pages)

        # -------------------------------------------------
        # Generate embeddings
        # -------------------------------------------------

        embeddings = []

        for chunk in chunks:
            embedding = generate_embedding(
                chunk["text"]
            )

            embeddings.append(embedding)

        # -------------------------------------------------
        # Store vectors
        # -------------------------------------------------

        chunk_count = add_documents(
            chunks=chunks,
            embeddings=embeddings,
            user_id=user_id,
            document_id=document_id,
        )

        # -------------------------------------------------
        # Update database
        # -------------------------------------------------

        (
            supabase
            .table("documents")
            .update({
                "page_count": len(pages),
                "chunk_count": chunk_count,
                "status": "ready",
            })
            .eq("id", document_id)
            .eq("user_id", user_id)
            .execute()
        )

        return {
            "message": "Document uploaded successfully",
            "document_id": document_id,
            "filename": file.filename,
            "pages": len(pages),
            "chunks": chunk_count,
        }

    except Exception as error:
        # -------------------------------------------------
        # Mark database record as failed
        # -------------------------------------------------

        if database_record_created:
            try:
                (
                    supabase
                    .table("documents")
                    .update({
                        "status": "failed",
                    })
                    .eq("id", document_id)
                    .eq("user_id", user_id)
                    .execute()
                )

            except Exception:
                pass

        # -------------------------------------------------
        # Remove orphaned Storage file
        # -------------------------------------------------

        elif storage_uploaded:
            try:
                supabase.storage.from_(
                    "documents"
                ).remove([
                    storage_path
                ])

            except Exception:
                pass

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    finally:
        # -------------------------------------------------
        # Delete temporary local PDF
        # -------------------------------------------------

        if file_path.exists():
            file_path.unlink()


# =====================================================
# CHAT
# =====================================================

@app.post("/chat")
def chat(
    request: ChatRequest,
    user=Depends(get_current_user),
):
    user_id = str(user.id)

    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty",
        )

    result = ask_question(
        question=request.question,
        user_id=user_id,
    )

    return result


# =====================================================
# GET USER DOCUMENTS
# =====================================================

@app.get("/documents")
def get_documents(
    user=Depends(get_current_user),
):
    user_id = str(user.id)

    result = (
        supabase
        .table("documents")
        .select("*")
        .eq(
            "user_id",
            user_id,
        )
        .order(
            "created_at",
            desc=True,
        )
        .execute()
    )

    return {
        "documents": result.data or []
    }


# =====================================================
# ADMIN - GET ALL DOCUMENTS
# =====================================================

@app.get("/admin/documents")
def get_admin_documents(
    admin=Depends(get_current_admin),
):
    try:
        result = (
            supabase
            .table("documents")
            .select("*")
            .order(
                "created_at",
                desc=True,
            )
            .execute()
        )

        documents = result.data or []

        return {
            "documents": documents,
            "total": len(documents),
        }

    except Exception as error:
        print(
            "Admin documents error:",
            str(error),
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to load admin documents",
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
        # 1. Find the document
        # ---------------------------------------------

        result = (
            supabase
            .table("documents")
            .select("*")
            .eq("id", document_id)
            .execute()
        )

        documents = result.data or []

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
        # 3. Delete vectors from ChromaDB
        # ---------------------------------------------

        delete_document(
            user_id=document_owner_id,
            document_id=document_id,
        )

        # ---------------------------------------------
        # 4. Delete PDF from Supabase Storage
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
            .eq("id", document_id)
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


# =====================================================
# DELETE USER DOCUMENT
# =====================================================

@app.delete("/documents/{document_id}")
def remove_document(
    document_id: str,
    user=Depends(get_current_user),
):
    user_id = str(user.id)

    # -------------------------------------------------
    # Find document
    # -------------------------------------------------

    result = (
        supabase
        .table("documents")
        .select("*")
        .eq(
            "id",
            document_id,
        )
        .eq(
            "user_id",
            user_id,
        )
        .execute()
    )

    documents = result.data or []

    if not documents:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    document = documents[0]

    # -------------------------------------------------
    # Delete vectors from ChromaDB
    # -------------------------------------------------

    delete_document(
        user_id=user_id,
        document_id=document_id,
    )

    # -------------------------------------------------
    # Delete PDF from Supabase Storage
    # -------------------------------------------------

    storage_path = document.get("file_path")

    if storage_path:
        supabase.storage.from_(
            "documents"
        ).remove([
            storage_path
        ])

    # -------------------------------------------------
    # Delete database record
    # -------------------------------------------------

    (
        supabase
        .table("documents")
        .delete()
        .eq(
            "id",
            document_id,
        )
        .eq(
            "user_id",
            user_id,
        )
        .execute()
    )

    return {
        "message": "Document deleted successfully"
    }


# =====================================================
# DASHBOARD
# =====================================================

@app.get("/dashboard")
def dashboard(
    user=Depends(get_current_user),
):
    user_id = str(user.id)

    result = (
        supabase
        .table("documents")
        .select("*")
        .eq(
            "user_id",
            user_id,
        )
        .execute()
    )

    documents = result.data or []

    total_documents = len(documents)

    total_chunks = sum(
        document.get(
            "chunk_count",
            0,
        ) or 0
        for document in documents
    )

    return {
        "total_documents": total_documents,
        "total_chunks": total_chunks,
        "documents": documents,
    }
