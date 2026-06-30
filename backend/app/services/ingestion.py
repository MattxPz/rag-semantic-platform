import uuid

import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.database import SessionLocal
from app.models.chunk import Chunk
from app.models.document import Document
from app.services.embeddings import generate_embedding

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
BLOCK_SEPARATOR = "\n\n"


def extract_pages_from_pdf(file_path: str) -> tuple[list[dict], float, float]:
    """
    Opens a PDF and returns:
      - a list of pages, each with its text blocks (text + bounding box)
      - the page width and height in PDF points (assumes a uniform page
        size, true for virtually all technical reports)
    Pages with no extractable text are skipped.
    """
    doc = fitz.open(file_path)
    page_width = float(doc[0].rect.width) if doc.page_count > 0 else 0.0
    page_height = float(doc[0].rect.height) if doc.page_count > 0 else 0.0

    pages = []
    for page_num, page in enumerate(doc, start=1):
        raw_blocks = page.get_text("blocks")  # (x0, y0, x1, y1, text, block_no, block_type)
        blocks = []
        for x0, y0, x1, y1, text, _block_no, block_type in raw_blocks:
            if block_type != 0:  # 0 = text block; skip images/drawings
                continue
            text = text.strip()
            if text:
                blocks.append({"bbox": [x0, y0, x1, y1], "text": text})
        if blocks:
            pages.append({"page_number": page_num, "blocks": blocks})

    doc.close()
    return pages, page_width, page_height


def _join_blocks_with_offsets(blocks: list[dict]) -> tuple[str, list[dict]]:
    """
    Joins block texts into one string and records each block's character
    range within it, so a chunk's start_index (from the splitter) can later
    be matched back to the original block bounding boxes.
    """
    parts = []
    offset_blocks = []
    cursor = 0
    for block in blocks:
        start = cursor
        parts.append(block["text"])
        cursor += len(block["text"])
        offset_blocks.append({"start": start, "end": cursor, "bbox": block["bbox"]})
        cursor += len(BLOCK_SEPARATOR)
    return BLOCK_SEPARATOR.join(parts), offset_blocks


def _bboxes_in_range(offset_blocks: list[dict], start: int, end: int) -> list[list[float]]:
    """Returns the bounding boxes of every block overlapping [start, end)."""
    return [b["bbox"] for b in offset_blocks if b["start"] < end and b["end"] > start]


def chunk_pages(pages: list[dict]) -> list[dict]:
    """
    Splits each page's text into overlapping chunks, attaching the bounding
    boxes of every text block each chunk overlaps with.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        add_start_index=True,
    )

    chunks = []
    for page in pages:
        page_text, offset_blocks = _join_blocks_with_offsets(page["blocks"])
        for split_doc in splitter.create_documents([page_text]):
            start = split_doc.metadata["start_index"]
            end = start + len(split_doc.page_content)
            bboxes = _bboxes_in_range(offset_blocks, start, end)
            chunks.append({
                "content": split_doc.page_content,
                "page_number": page["page_number"],
                "bbox": bboxes or None,
            })
    return chunks


def process_document_task(document_id: uuid.UUID, file_path: str) -> None:
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return
        doc.status = "processing"
        db.commit()

        pages, page_width, page_height = extract_pages_from_pdf(file_path)
        doc.page_width = page_width
        doc.page_height = page_height

        if not pages:
            doc.status = "error"
            db.commit()
            return

        doc.num_pages = len(pages)
        db.commit()

        chunks_data = chunk_pages(pages)

        for chunk_data in chunks_data:
            embedding_vector = generate_embedding(chunk_data["content"])
            chunk = Chunk(
                document_id=document_id,
                content=chunk_data["content"],
                page_number=chunk_data["page_number"],
                bbox=chunk_data["bbox"],
                embedding=embedding_vector,
                token_count=len(chunk_data["content"].split()),
            )
            db.add(chunk)

        doc.status = "ready"
        db.commit()

    except Exception:
        db.rollback()
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