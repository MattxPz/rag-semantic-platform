import uuid

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    document_ids: list[uuid.UUID] | None = None
    conversation_id: uuid.UUID | None = None


class SourceChunk(BaseModel):
    chunk_id: str
    page_number: int
    content_preview: str
    bbox: list[list[float]] | None = None


class ChatEvent(BaseModel):
    type: str
    content: str | None = None
    sources: list[SourceChunk] | None = None
    conversation_id: str | None = None
