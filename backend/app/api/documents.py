import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentOut
from app.core.queue import task_queue
from app.services.ingestion import process_document_task

router = APIRouter(prefix="/documents", tags=["documents"])

STORAGE = Path(settings.storage_path)


@router.post("/", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted.",
        )

    # Generate unique ID and persist the file
    doc_id = uuid.uuid4()
    STORAGE.mkdir(parents=True, exist_ok=True)
    file_path = STORAGE / f"{doc_id}.pdf"

    contents = await file.read()
    file_path.write_bytes(contents)

    # Create DB record
    doc = Document(
        id=doc_id,
        owner_id=current_user.id,
        filename=file.filename,
        file_path=str(file_path),
        status="pending",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Enqueue background processing on the RQ worker.
    # job_timeout is generous because embedding a large PDF on CPU is slow.
    task_queue.enqueue(
        process_document_task,
        doc_id,
        str(file_path),
        job_timeout="30m",
    )

    return doc


@router.get("/", response_model=list[DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Document).filter(Document.owner_id == current_user.id).all()


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(
    doc_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.owner_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return doc


@router.get("/{doc_id}/file")
def serve_document_file(
    doc_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns the raw PDF file — used by the PDF viewer in Phase 5."""
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.owner_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    file_path = Path(doc.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk.")

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=doc.filename,
    )