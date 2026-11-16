"""
SQLAlchemy ORM models representing the complete Agentic RAG state, persistence, and execution traces.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    Index
)
from sqlalchemy.orm import relationship
from app.db.base import Base, VectorType
from app.core.config import settings


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False, index=True)
    file_type = Column(String(32), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    content_hash = Column(String(64), nullable=False, unique=True, index=True)
    status = Column(String(32), default="processing", nullable=False, index=True)
    total_chunks = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True)
    original_text = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False)
    embedding = Column(VectorType(dim=settings.VECTOR_DIMENSION), nullable=True)
    metadata_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    document = relationship("Document", back_populates="chunks")

    __table_args__ = (
        Index("idx_doc_chunk_idx", "document_id", "chunk_index"),
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(32), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    citations_json = Column(JSON, default=list, nullable=False)
    confidence_label = Column(String(32), default="supported", nullable=False)
    token_count = Column(Integer, default=0, nullable=False)
    execution_id = Column(String(36), ForeignKey("query_executions.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")
    execution = relationship("QueryExecution")


class QueryExecution(Base):
    __tablename__ = "query_executions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), nullable=True, index=True)
    trace_id = Column(String(64), nullable=False, index=True)
    original_query = Column(Text, nullable=False)
    rewritten_queries = Column(JSON, default=list, nullable=False)
    retrieval_method = Column(String(64), default="hybrid", nullable=False)
    bm25_count = Column(Integer, default=0, nullable=False)
    dense_count = Column(Integer, default=0, nullable=False)
    fused_count = Column(Integer, default=0, nullable=False)
    reranked_count = Column(Integer, default=0, nullable=False)
    evidence_sufficient = Column(Boolean, default=True, nullable=False)
    selected_context_tokens = Column(Integer, default=0, nullable=False)
    generation_attempts = Column(Integer, default=1, nullable=False)
    faithfulness_score = Column(Float, nullable=True)
    citation_valid = Column(Boolean, default=True, nullable=False)
    fallback_reason = Column(String(128), nullable=True)
    final_status = Column(String(32), default="success", nullable=False)
    latency_ms = Column(Float, default=0.0, nullable=False)
    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    estimated_cost_usd = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    retrieval_results = relationship("RetrievalResult", back_populates="execution", cascade="all, delete-orphan")


class RetrievalResult(Base):
    __tablename__ = "retrieval_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    execution_id = Column(String(36), ForeignKey("query_executions.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_id = Column(String(36), nullable=False, index=True)
    document_id = Column(String(36), nullable=False)
    filename = Column(String(255), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True)
    sparse_rank = Column(Integer, nullable=True)
    dense_rank = Column(Integer, nullable=True)
    rrf_score = Column(Float, default=0.0, nullable=False)
    rerank_score = Column(Float, nullable=True)
    selected_for_context = Column(Boolean, default=False, nullable=False)
    chunk_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    execution = relationship("QueryExecution", back_populates="retrieval_results")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    dataset_name = Column(String(128), default="default_test_suite", nullable=False)
    configuration_name = Column(String(128), default="hybrid_with_rerank", nullable=False)
    status = Column(String(32), default="pending", nullable=False, index=True)
    sample_count = Column(Integer, default=0, nullable=False)
    avg_faithfulness = Column(Float, nullable=True)
    avg_answer_relevancy = Column(Float, nullable=True)
    avg_context_precision = Column(Float, nullable=True)
    avg_context_recall = Column(Float, nullable=True)
    total_duration_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    results = relationship("EvaluationResult", back_populates="run", cascade="all, delete-orphan")


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(36), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    ground_truth = Column(Text, nullable=False)
    generated_answer = Column(Text, nullable=False)
    retrieved_contexts = Column(JSON, default=list, nullable=False)
    faithfulness = Column(Float, nullable=True)
    answer_relevancy = Column(Float, nullable=True)
    context_precision = Column(Float, nullable=True)
    context_recall = Column(Float, nullable=True)
    metadata_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    run = relationship("EvaluationRun", back_populates="results")
