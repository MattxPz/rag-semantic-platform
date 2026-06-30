"""add hnsw index on chunks embedding

Revision ID: b9090ed8774c
Revises: 8a614f987a48
Create Date: 2026-06-29 19:29:31.103877

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b9090ed8774c'
down_revision: Union[str, Sequence[str], None] = '8a614f987a48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # HNSW index with cosine distance — optimal for nomic-embed-text (768-dim)
    # m=16 and ef_construction=64 are the recommended defaults for most RAG use cases
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw_idx "
            "ON chunks USING hnsw (embedding vector_cosine_ops) "
            "WITH (m = 16, ef_construction = 64)"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS chunks_embedding_hnsw_idx"))
