import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import SessionLocal, get_db
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.message import Message
from app.models.user import User
from app.schemas.conversation import ChatRequest
from app.services.embeddings import generate_embedding
from app.services.rag import build_search_query, stream_rag_response
from app.services.retrieval import retrieve_relevant_chunks

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/")
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ── 1. Validate requested document_ids belong to this user ───────────────
    if request.document_ids:
        for doc_id in request.document_ids:
            doc = db.query(Document).filter(
                Document.id == doc_id,
                Document.owner_id == current_user.id,
            ).first()
            if not doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document {doc_id} not found.",
                )
            if doc.status != "ready":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Document {doc_id} is not ready yet (status: {doc.status}).",
                )

    # ── 2. Resolve or create conversation ────────────────────────────────────
    if request.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id,
            Conversation.owner_id == current_user.id,
        ).first()
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )
    else:
        conversation = Conversation(owner_id=current_user.id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # ── 3. Load prior messages BEFORE adding the new one (this is the history) ─
    history = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
        .all()
    )

    # ── 4. Persist user message ───────────────────────────────────────────────
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.question,
    )
    db.add(user_message)
    db.commit()

    # ── 5. Embed a search query that folds in recent context ─────────────────
    search_query = build_search_query(request.question, history)
    query_embedding = generate_embedding(search_query)

    # ── 6. Retrieve relevant chunks ───────────────────────────────────────────
    chunks = retrieve_relevant_chunks(
        query_embedding=query_embedding,
        db=db,
        owner_id=current_user.id,
        document_ids=request.document_ids,
        top_k=settings.top_k_chunks,
    )

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No relevant content found. Make sure at least one document is ready.",
        )

    source_chunk_ids = [chunk.id for chunk in chunks]
    conversation_id = conversation.id

    # ── 7. Build streaming generator ─────────────────────────────────────────
    def generate():
        collected_tokens: list[str] = []

        for event in stream_rag_response(request.question, chunks, history):
            yield event

            try:
                if event.startswith("data: "):
                    data = json.loads(event[6:].strip())
                    if data.get("type") == "token":
                        collected_tokens.append(data.get("content", ""))
            except Exception:
                pass

        save_db = SessionLocal()
        try:
            assistant_message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content="".join(collected_tokens),
                source_chunk_ids=source_chunk_ids,
            )
            save_db.add(assistant_message)
            save_db.commit()
        except Exception:
            save_db.rollback()
        finally:
            save_db.close()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "X-Conversation-Id": str(conversation_id),
        },
    )


@router.get("/conversations")
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversations = (
        db.query(Conversation)
        .filter(Conversation.owner_id == current_user.id)
        .order_by(Conversation.created_at.desc())
        .all()
    )
    return [
        {"id": str(c.id), "created_at": c.created_at.isoformat()}
        for c in conversations
    ]