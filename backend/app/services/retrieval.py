import uuid

from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.models.document import Document


def retrieve_relevant_chunks(
    query_embedding: list[float],
    db: Session,
    owner_id: uuid.UUID,
    document_ids: list[uuid.UUID] | None = None,
    top_k: int = 5,
) -> list[Chunk]:
    """
    Searches for the top-k chunks most similar to query_embedding using
    cosine distance (<=>). Always scoped to the requesting user's documents.
    """
    # If caller didn't specify documents, use ALL of the user's ready documents
    if document_ids:
        effective_ids = document_ids
    else:
        effective_ids = [
            row.id
            for row in db.query(Document.id).filter(
                Document.owner_id == owner_id,
                Document.status == "ready",
            ).all()
        ]

    if not effective_ids:
        return []

    results = (
        db.query(Chunk)
        .filter(
            Chunk.document_id.in_(effective_ids),
            Chunk.embedding.isnot(None),
        )
        .order_by(Chunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
        .all()
    )
    return results