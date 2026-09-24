import uuid

from pathlib import Path

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Depends,
    HTTPException
)

from fastapi.middleware.cors import (
    CORSMiddleware
)

from pydantic import BaseModel


from auth import (
    get_current_user,
    supabase
)


from config import (
    DOCUMENT_DIR
)


from ingestion.pdf_loader import (
    extract_pdf_pages
)


from ingestion.chunker import (
    create_chunks
)


from rag.embeddings import (
    generate_embedding
)


from rag.vector_store import (
    add_documents,
    delete_document
)


from rag.rag_engine import (
    ask_question
)


# =====================================================
# APP
# =====================================================

app = FastAPI(

    title="Enterprise GPT API",

    version="1.0.0"
)


# =====================================================
# CORS
# =====================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=[
        "http://localhost:3000"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


# =====================================================
# Request model
# =====================================================

class ChatRequest(BaseModel):

    question: str


# =====================================================
# HOME
# =====================================================

@app.get("/")
def home():

    return {

        "message":
            "Enterprise GPT API is running",

        "status":
            "success"
    }


# =====================================================
# UPLOAD PDF
# =====================================================

@app.post("/upload")
async def upload_document(

    file: UploadFile = File(...),

    user=Depends(get_current_user)

):

    # -----------------------------------------
    # Validate file
    # -----------------------------------------

    if not file.filename:

        raise HTTPException(

            status_code=400,

            detail="Filename is missing"
        )


    if not file.filename.lower().endswith(
        ".pdf"
    ):

        raise HTTPException(

            status_code=400,

            detail="Only PDF files are supported"
        )


    # -----------------------------------------
    # User ID
    # -----------------------------------------

    user_id = str(
        user.id
    )


    # -----------------------------------------
    # Document ID
    # -----------------------------------------

    document_id = str(
        uuid.uuid4()
    )


    # -----------------------------------------
    # Safe filename
    # -----------------------------------------

    safe_filename = (

        f"{user_id}_"
        f"{document_id}_"
        f"{file.filename}"
    )


    file_path = (
        DOCUMENT_DIR /
        safe_filename
    )


    # -----------------------------------------
    # Save PDF
    # -----------------------------------------

    contents = await file.read()


    with open(
        file_path,
        "wb"
    ) as output_file:

        output_file.write(
            contents
        )


    # -----------------------------------------
    # Database record
    # -----------------------------------------

    supabase.table(
        "documents"
    ).insert({

        "id":
            document_id,

        "user_id":
            user_id,

        "file_name":
            file.filename,

        "file_path":
            str(file_path),

        "status":
            "processing"

    }).execute()


    try:

        # -------------------------------------
        # Extract pages
        # -------------------------------------

        pages = extract_pdf_pages(
            file_path
        )


        # -------------------------------------
        # Create chunks
        # -------------------------------------

        chunks = create_chunks(
            pages
        )


        # -------------------------------------
        # Create embeddings
        # -------------------------------------

        embeddings = []


        for chunk in chunks:

            embedding = generate_embedding(

                chunk["text"]
            )

            embeddings.append(
                embedding
            )


        # -------------------------------------
        # Save vectors
        # -------------------------------------

        chunk_count = add_documents(

            chunks=chunks,

            embeddings=embeddings,

            user_id=user_id,

            document_id=document_id
        )


        # -------------------------------------
        # Update DB
        # -------------------------------------

        supabase.table(
            "documents"
        ).update({

            "page_count":
                len(pages),

            "chunk_count":
                chunk_count,

            "status":
                "ready"

        }).eq(
            "id",
            document_id
        ).eq(
            "user_id",
            user_id
        ).execute()


        return {

            "message":
                "Document uploaded successfully",

            "document_id":
                document_id,

            "filename":
                file.filename,

            "pages":
                len(pages),

            "chunks":
                chunk_count
        }


    except Exception as error:

        supabase.table(
            "documents"
        ).update({

            "status":
                "failed"

        }).eq(
            "id",
            document_id
        ).execute()


        raise HTTPException(

            status_code=500,

            detail=str(error)
        )


# =====================================================
# CHAT
# =====================================================

@app.post("/chat")
def chat(

    request: ChatRequest,

    user=Depends(get_current_user)

):

    user_id = str(
        user.id
    )


    if not request.question.strip():

        raise HTTPException(

            status_code=400,

            detail=
                "Question cannot be empty"
        )


    result = ask_question(

        question=
            request.question,

        user_id=
            user_id
    )


    return result


# =====================================================
# GET DOCUMENTS
# =====================================================

@app.get("/documents")
def get_documents(

    user=Depends(get_current_user)

):

    user_id = str(
        user.id
    )


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
            result.data
    }


# =====================================================
# DELETE DOCUMENT
# =====================================================

@app.delete(
    "/documents/{document_id}"
)
def remove_document(

    document_id: str,

    user=Depends(get_current_user)

):

    user_id = str(
        user.id
    )


    # -----------------------------------------
    # Find document
    # -----------------------------------------

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


    documents = result.data


    if not documents:

        raise HTTPException(

            status_code=404,

            detail="Document not found"
        )


    document = documents[0]


    # -----------------------------------------
    # Delete vectors
    # -----------------------------------------

    delete_document(

        user_id=user_id,

        document_id=document_id
    )


    # -----------------------------------------
    # Delete PDF
    # -----------------------------------------

    file_path = Path(
        document["file_path"]
    )


    if file_path.exists():

        file_path.unlink()


    # -----------------------------------------
    # Delete database record
    # -----------------------------------------

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


# =====================================================
# DASHBOARD
# =====================================================

@app.get("/dashboard")
def dashboard(

    user=Depends(get_current_user)

):

    user_id = str(
        user.id
    )


    result = (

        supabase

        .table("documents")

        .select("*")

        .eq(
            "user_id",
            user_id
        )

        .execute()
    )


    documents = result.data


    total_documents = len(
        documents
    )


    total_chunks = sum(

        document.get(
            "chunk_count",
            0
        )

        for document in documents
    )


    return {

        "total_documents":
            total_documents,

        "total_chunks":
            total_chunks,

        "documents":
            documents
    }
