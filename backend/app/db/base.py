"""
SQLAlchemy Base class and custom dialect-aware column types.
"""
import json
from typing import Any, List
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator, TEXT, JSON
from app.core.config import settings

try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False


class Base(DeclarativeBase):
    pass


class VectorType(TypeDecorator):
    """
    Dialect-aware vector column type.
    Uses pgvector's Vector type on PostgreSQL, and JSON-encoded list of floats on SQLite/other dialects.
    """
    impl = JSON
    cache_ok = True

    def __init__(self, dim: int = 384, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and PGVECTOR_AVAILABLE:
            return dialect.type_descriptor(Vector(self.dim))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, list):
            return value
        return list(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                # Handle postgres string representation like '[0.1, 0.2]'
                cleaned = value.strip("[]").split(",")
                return [float(x.strip()) for x in cleaned if x.strip()]
        return list(value)
