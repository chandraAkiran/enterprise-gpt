from config import (
    CHUNK_SIZE,
    CHUNK_OVERLAP
)


def create_chunks(
    pages,
    chunk_size=CHUNK_SIZE,
    overlap=CHUNK_OVERLAP
):

    chunks = []

    for page in pages:

        text = page["text"]

        start = 0

        while start < len(text):

            end = start + chunk_size

            chunk_text = text[start:end]

            if chunk_text.strip():

                chunks.append({
                    "text": chunk_text,
                    "page": page["page"],
                    "source": page["source"]
                })

            start = end - overlap

            if start < 0:
                start = 0

    return chunks
