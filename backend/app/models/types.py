"""
Custom SQLAlchemy types that work on both PostgreSQL (production) and
SQLite (test suite). Postgres uses its native UUID/JSONB/ARRAY/Vector types;
SQLite falls back to portable equivalents with explicit value conversion.
"""

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import CHAR, JSON, TypeDecorator

EMBEDDING_DIM = 768  # nomic-embed-text output dimensions


class GUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's native UUID when available, otherwise stores as a
    32-character hex string (CHAR) in SQLite. Handles converting the Python
    uuid.UUID object to/from the stored representation.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        # Python -> DB
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value  # psycopg handles UUID objects natively
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(str(value))
        return value.hex  # store as plain hex string in SQLite

    def process_result_value(self, value, dialect):
        # DB -> Python
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


class GUIDArray(TypeDecorator):
    """List of UUIDs. Native ARRAY(UUID) in Postgres, JSON list in SQLite."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(ARRAY(PG_UUID(as_uuid=True)))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value  # list of UUID objects, handled natively
        return [str(item) for item in value]  # JSON-serializable strings for SQLite

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return [uuid.UUID(item) if not isinstance(item, uuid.UUID) else item for item in value]


class JSONBType(TypeDecorator):
    """JSONB in Postgres, generic JSON in SQLite."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


class VectorType(TypeDecorator):
    """pgvector Vector in Postgres, JSON list in SQLite (no similarity search in tests)."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(EMBEDDING_DIM))
        return dialect.type_descriptor(JSON())
