import uuid

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from auth import get_current_user, supabase
from config import DOCUMENT_DIR
from ingestion.pdf_loader import extract_pdf_pages
from ingestion.chunker import create_chunks
from rag.embeddings import generate_embedding
from rag.vector_store import add_documents, delete_document
from rag.rag_engine import ask_question


app = FastAPI(
    title="Enterprise GPT API",
    version="1.0.0",
)

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


class ChatRequest(BaseModel):
    question: str


@app.get("/")
def home():
    return {
        "message": "Enterprise GPT API is running",
        "status": "success",
    }


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported",
        )

    user_id = str(user.id)
    document_id = str(uuid.uuid4())

    safe_filename = f"{user_id}_{document_id}_{file.filename}"
    file_path = DOCUMENT_DIR / safe_filename

    contents = await file.read()

    with open(file_path, "wb") as output_file:
        output_file.write(contents)

    storage_path = f"{user_id}/{document_id}_{file.filename}"

    storage_uploaded = False
    database_record_created = False

    try:
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
        database_record_created = True

        pages = extract_pdf_pages(file_path)
        chunks = create_chunks(pages)

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
        }).eq(
            "id", document_id
        ).eq(
            "user_id", user_id
        ).execute()

        return {
            "message": "Document uploaded successfully",
            "document_id": document_id,
            "filename": file.filename,
            "pages": len(pages),
            "chunks": chunk_count,
        }

    except Exception as error:
        if database_record_created:
            try:
                supabase.table("documents").update({
                    "status": "failed",
                }).eq(
                    "id", document_id
                ).eq(
                    "user_id", user_id
                ).execute()
            except Exception:
                pass
        elif storage_uploaded:
            try:
                supabase.storage.from_("documents").remove([storage_path])
            except Exception:
                pass

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    finally:
        if file_path.exists():
            file_path.unlink()


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

    return ask_question(
        question=request.question,
        user_id=user_id,
    )


@app.get("/documents")
def get_documents(
    user=Depends(get_current_user),
):
    user_id = str(user.id)

    result = (
        supabase
        .table("documents")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    return {"documents": result.data}


@app.delete("/documents/{document_id}")
def remove_document(
    document_id: str,
    user=Depends(get_current_user),
):
    user_id = str(user.id)

    result = (
        supabase
        .table("documents")
        .select("*")
        .eq("id", document_id)
        .eq("user_id", user_id)
        .execute()
    )

    documents = result.data

    if not documents:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    document = documents[0]

    delete_document(
        user_id=user_id,
        document_id=document_id,
    )

    storage_path = document.get("file_path")
    if storage_path:
        supabase.storage.from_("documents").remove([storage_path])

    (
        supabase
        .table("documents")
        .delete()
        .eq("id", document_id)
        .eq("user_id", user_id)
        .execute()
    )

    return {"message": "Document deleted successfully"}


@app.get("/dashboard")
def dashboard(
    user=Depends(get_current_user),
):
    user_id = str(user.id)

    result = (
        supabase
        .table("documents")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )

    documents = result.data

    total_documents = len(documents)
    total_chunks = sum(
        document.get("chunk_count", 0) or 0
        for document in documents
    )

    return {
        "total_documents": total_documents,
        "total_chunks": total_chunks,
        "documents": documents,
    }
