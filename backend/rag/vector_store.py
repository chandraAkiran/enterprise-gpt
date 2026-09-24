import chromadb

from config import VECTOR_DIR


# -----------------------------------------
# Chroma client
# -----------------------------------------

client = chromadb.PersistentClient(
    path=str(VECTOR_DIR)
)


# -----------------------------------------
# Collection
# -----------------------------------------

collection = client.get_or_create_collection(
    name="enterprise_knowledge"
)


# -----------------------------------------
# Add chunks
# -----------------------------------------

def add_documents(
    chunks,
    embeddings,
    user_id,
    document_id
):

    ids = []

    documents = []

    metadatas = []

    vectors = []


    for index, chunk in enumerate(chunks):

        chunk_id = (
            f"{user_id}_"
            f"{document_id}_"
            f"{index}"
        )

        ids.append(chunk_id)

        documents.append(
            chunk["text"]
        )

        metadatas.append({

            "user_id": user_id,

            "document_id": document_id,

            "source": chunk["source"],

            "page": chunk["page"]
        })

        vectors.append(
            embeddings[index]
        )


    if not ids:

        return 0


    collection.add(

        ids=ids,

        documents=documents,

        embeddings=vectors,

        metadatas=metadatas
    )


    return len(ids)


# -----------------------------------------
# Search
# -----------------------------------------

def search_documents(
    query_embedding,
    user_id,
    top_k=5
):

    results = collection.query(

        query_embeddings=[
            query_embedding
        ],

        n_results=top_k,

        where={
            "user_id": user_id
        }
    )

    return results


# -----------------------------------------
# Delete document vectors
# -----------------------------------------

def delete_document(
    user_id,
    document_id
):

    collection.delete(

        where={
            "$and": [

                {
                    "user_id": user_id
                },

                {
                    "document_id": document_id
                }
            ]
        }
    )


# -----------------------------------------
# Count user chunks
# -----------------------------------------

def get_document_count(user_id):

    result = collection.get(

        where={
            "user_id": user_id
        }
    )

    return len(
        result["ids"]
    )
