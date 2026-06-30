"""add page dimensions and block-level bbox storage

Revision ID: 756e129ae201
Revises: b9090ed8774c
Create Date: 2026-06-30 08:48:19.693765

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '756e129ae201'
down_revision: Union[str, Sequence[str], None] = 'b9090ed8774c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Store each document's page size (in PDF points) to scale bounding
    # boxes correctly when rendering highlights in the frontend.
    op.add_column("documents", sa.Column("page_width", sa.Float(), nullable=True))
    op.add_column("documents", sa.Column("page_height", sa.Float(), nullable=True))

    # bbox now stores a list of [x0, y0, x1, y1] rectangles (one per text
    # block) instead of a single full-page rectangle — JSONB fits this
    # variable-length, nested structure better than a flat float array.
    # Existing rows lose their old (full-page) bbox value.
    op.drop_column("chunks", "bbox")
    op.add_column("chunks", sa.Column("bbox", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("chunks", "bbox")
    op.add_column("chunks", sa.Column("bbox", postgresql.ARRAY(sa.Float()), nullable=True))

    op.drop_column("documents", "page_height")
    op.drop_column("documents", "page_width")
