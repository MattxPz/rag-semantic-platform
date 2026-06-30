import uuid

import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.database import SessionLocal
from app.models.chunk import Chunk
from app.models.document import Document
from app.services.embeddings import generate_embedding

CHUNK_SIZE = 800    # characters per chunk
CHUNK_OVERLAP = 100  # overlap between consecutive chunks


def extract_pages_from_pdf(file_path: str) -> list[dict]:
    """
    Opens a PDF and returns a list of pages with their text and bounding box.
    Pages with no extractable text are skipped.
    """
    doc = fitz.open(file_path)
    pages = []
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text().strip()
        if text:
            pages.append({
                "page_number": page_num,
                "text": text,
                # Full-page bbox — will be refined to block-level in Phase 5
                "bbox": [0.0, 0.0, float(page.rect.width), float(page.rect.height)],
            })
    doc.close()
    return pages


def chunk_pages(pages: list[dict]) -> list[dict]:
    """
    Splits each page's text into overlapping chunks, preserving page metadata.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )
    chunks = []
    for page in pages:
        texts = splitter.split_text(page["text"])
        for text in texts:
            chunks.append({
                "content": text,
                "page_number": page["page_number"],
                "bbox": page["bbox"],
            })
    return chunks


def process_document_task(document_id: uuid.UUID, file_path: str) -> None:
    """
    Background task that runs after a PDF is uploaded.
    Pipeline: extract text → chunk → generate embeddings → save to DB.
    Creates its own DB session (the request session is already closed at this point).
    """
    db = SessionLocal()
    try:
        # 1. Mark as processing
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return
        doc.status = "processing"
        db.commit()

        # 2. Extract text per page
        pages = extract_pages_from_pdf(file_path)

        if not pages:
            doc.status = "error"
            db.commit()
            return

        doc.num_pages = len(pages)
        db.commit()

        # 3. Chunk all pages
        chunks_data = chunk_pages(pages)

        # 4. Generate embedding per chunk and accumulate
        for chunk_data in chunks_data:
            embedding_vector = generate_embedding(chunk_data["content"])
            chunk = Chunk(
                document_id=document_id,
                content=chunk_data["content"],
                page_number=chunk_data["page_number"],
                bbox=chunk_data["bbox"],
                embedding=embedding_vector,
                # Word count as an approximation of token count
                token_count=len(chunk_data["content"].split()),
            )
            db.add(chunk)

        # 5. Commit all chunks + mark as ready in one transaction
        doc.status = "ready"
        db.commit()

    except Exception:
        db.rollback()
        # Best-effort: try to mark the document as failed
        try:
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.status = "error"
                db.commit()
        except Exception:
            pass
        raise
    finally:
        db.close()