"""
Typed workflow state for the Agentic RAG LangGraph orchestration.
Maintains execution lineage, retrieval results, rewrites, and verification metrics.
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from app.schemas.retrieval import RetrievedChunk
from app.schemas.chat import AnswerResponse, Citation


class AgenticRAGState(BaseModel):
    # Core Query & Identity
    trace_id: str
    query: str
    original_query: str
    query_type: Optional[str] = "factual"  # factual, conceptual, out_of_scope
    conversation_id: Optional[str] = None
    retrieval_method: str = "hybrid"

    # Iteration & Budget Counters
    rewrite_count: int = 0
    max_rewrites: int = 2
    generation_attempts: int = 0
    max_generations: int = 2
    context_token_budget: int = 2500
    rewritten_queries: List[str] = Field(default_factory=list)

    # Retrieval State
    dense_candidates: List[RetrievedChunk] = Field(default_factory=list)
    sparse_candidates: List[RetrievedChunk] = Field(default_factory=list)
    fused_candidates: List[RetrievedChunk] = Field(default_factory=list)
    reranked_candidates: List[RetrievedChunk] = Field(default_factory=list)
    selected_context: List[RetrievedChunk] = Field(default_factory=list)
    evidence_sufficient: bool = False
    retrieval_quality_score: float = 0.0

    # Generation & Validation State
    raw_generation_output: Optional[str] = None
    answer_response: Optional[AnswerResponse] = None
    output_valid: bool = False
    citation_valid: bool = False
    faithfulness_score: float = 0.0
    faithfulness_passed: bool = False
    validation_errors: List[str] = Field(default_factory=list)

    # Fallback & Final State
    fallback_reason: Optional[str] = None
    final_status: Literal["success", "fallback", "error"] = "success"
    error_message: Optional[str] = None

    # Telemetry
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    selected_context_tokens: int = 0
