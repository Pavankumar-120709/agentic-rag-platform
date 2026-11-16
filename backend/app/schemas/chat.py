"""
Pydantic schemas for Chat, Citations, Answer Responses, and Conversations.
"""
from datetime import datetime
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class Citation(BaseModel):
    document_id: str
    filename: str
    chunk_id: str
    page_number: Optional[int] = None
    quoted_text: str = Field(description="Exact verbatim excerpt from the source chunk supporting the claim.")


class AnswerResponse(BaseModel):
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    confidence_label: Literal["supported", "partially_supported", "insufficient_evidence"]
    evidence_summary: str
    warnings: List[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    conversation_id: Optional[str] = None
    retrieval_method: Optional[Literal["hybrid", "dense_only", "sparse_only"]] = "hybrid"
    max_rewrites: Optional[int] = 2
    context_token_budget: Optional[int] = 2500


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    role: str
    content: str
    citations: List[Citation] = Field(default_factory=list)
    confidence_label: str
    token_count: int
    execution_id: Optional[str] = None
    created_at: datetime


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationRead):
    messages: List[MessageRead] = Field(default_factory=list)


class ChatResponse(BaseModel):
    conversation_id: str
    message: MessageRead
    answer_response: AnswerResponse
    execution_id: str
    trace_id: str
    latency_ms: float
    token_usage: Dict[str, Any]
