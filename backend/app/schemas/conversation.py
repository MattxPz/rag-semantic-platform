import uuid
from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    # If None → searches across all the user's ready documents
    document_ids: list[uuid.UUID] | None = None
    # If None → creates a new conversation automatically
    conversation_id: uuid.UUID | None = None


class SourceChunk(BaseModel):
    chunk_id: str
    page_number: int
    content_preview: str  # first 150 chars, used by frontend highlighter


class ChatEvent(BaseModel):
    """Describes the shape of every SSE data payload."""
    type: str   # "sources" | "token" | "done" | "error"
    content: str | None = None
    sources: list[SourceChunk] | None = None
    conversation_id: str | None = None