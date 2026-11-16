"""
Pydantic schemas for Hybrid Retrieval, RRF Fusion, and Reranking outputs.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    chunk_index: int
    page_number: Optional[int] = None
    original_text: str
    token_count: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    sparse_score: Optional[float] = None
    sparse_rank: Optional[int] = None
    dense_score: Optional[float] = None
    dense_rank: Optional[int] = None
    rrf_score: Optional[float] = None
    rerank_score: Optional[float] = None


class HybridRetrievalResult(BaseModel):
    sparse_candidates: List[RetrievedChunk] = Field(default_factory=list)
    dense_candidates: List[RetrievedChunk] = Field(default_factory=list)
    fused_candidates: List[RetrievedChunk] = Field(default_factory=list)
    reranked_candidates: List[RetrievedChunk] = Field(default_factory=list)
    selected_context: List[RetrievedChunk] = Field(default_factory=list)
