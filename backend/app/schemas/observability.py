"""
Pydantic schemas for Metrics, Health, and Query Execution Traces.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class RetrievalResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    chunk_id: str
    document_id: str
    filename: str
    chunk_index: int
    page_number: Optional[int] = None
    sparse_rank: Optional[int] = None
    dense_rank: Optional[int] = None
    rrf_score: float
    rerank_score: Optional[float] = None
    selected_for_context: bool
    chunk_text: str


class QueryExecutionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: Optional[str] = None
    trace_id: str
    original_query: str
    rewritten_queries: List[str] = Field(default_factory=list)
    retrieval_method: str
    bm25_count: int
    dense_count: int
    fused_count: int
    reranked_count: int
    evidence_sufficient: bool
    selected_context_tokens: int
    generation_attempts: int
    faithfulness_score: Optional[float] = None
    citation_valid: bool
    fallback_reason: Optional[str] = None
    final_status: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    created_at: datetime
    retrieval_results: List[RetrievalResultRead] = Field(default_factory=list)


class SystemMetricsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    total_queries: int
    avg_latency_ms: float
    total_tokens_consumed: int
    estimated_total_cost_usd: float
    avg_faithfulness: Optional[float] = None
    avg_relevancy: Optional[float] = None
    retrieval_distribution: Dict[str, int] = Field(default_factory=dict)
