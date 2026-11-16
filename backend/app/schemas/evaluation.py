"""
Pydantic schemas for RAGAS and Offline Evaluation benchmarks.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class EvaluationSample(BaseModel):
    question: str
    ground_truth: str
    reference_contexts: Optional[List[str]] = Field(default_factory=list)


class EvaluationRunRequest(BaseModel):
    name: Optional[str] = "Benchmark Run"
    description: Optional[str] = None
    configuration_name: Optional[str] = "hybrid_with_rerank"
    custom_samples: Optional[List[EvaluationSample]] = None


class EvaluationResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    question: str
    ground_truth: str
    generated_answer: str
    retrieved_contexts: List[str] = Field(default_factory=list)
    faithfulness: Optional[float] = None
    answer_relevancy: Optional[float] = None
    context_precision: Optional[float] = None
    context_recall: Optional[float] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class EvaluationRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    dataset_name: str
    configuration_name: str
    status: str
    sample_count: int
    avg_faithfulness: Optional[float] = None
    avg_answer_relevancy: Optional[float] = None
    avg_context_precision: Optional[float] = None
    avg_context_recall: Optional[float] = None
    total_duration_seconds: Optional[float] = None
    created_at: datetime
    results: Optional[List[EvaluationResultRead]] = None
