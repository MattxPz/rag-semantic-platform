import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: uuid.UUID
    filename: str
    status: str
    num_pages: int | None
    page_width: float | None
    page_height: float | None
    uploaded_at: datetime

    model_config = {"from_attributes": True}