from pypdf import PdfReader


def clean_text(text):

    if not text:
        return ""

    text = text.replace("\x00", " ")

    text = " ".join(
        text.split()
    )

    return text


def extract_pdf_pages(file_path):

    reader = PdfReader(
        str(file_path)
    )

    pages = []

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):

        text = page.extract_text()

        text = clean_text(text)

        if text:

            pages.append({
                "text": text,
                "page": page_number,
                "source": file_path.name
            })

    return pages
