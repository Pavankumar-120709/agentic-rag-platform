"""
FastAPI router for Observability, System Metrics, and Query Execution Traces.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.db.models import Document, DocumentChunk, QueryExecution, EvaluationRun
from app.schemas.observability import QueryExecutionRead, SystemMetricsResponse

router = APIRouter(tags=["Observability"])


@router.get("/metrics", response_model=SystemMetricsResponse)
def get_system_metrics(db: Session = Depends(get_db)):
    """
    Returns aggregated system metrics including documents, chunks, query volume,
    latency averages, token consumption, and benchmark evaluation averages.
    """
    total_docs = db.query(func.count(Document.id)).scalar() or 0
    total_chunks = db.query(func.count(DocumentChunk.id)).scalar() or 0
    total_queries = db.query(func.count(QueryExecution.id)).scalar() or 0
    
    avg_latency = db.query(func.avg(QueryExecution.latency_ms)).scalar() or 0.0
    total_tokens = db.query(func.sum(QueryExecution.total_tokens)).scalar() or 0
    total_cost = db.query(func.sum(QueryExecution.estimated_cost_usd)).scalar() or 0.0

    avg_faithfulness = db.query(func.avg(EvaluationRun.avg_faithfulness)).filter(EvaluationRun.status == "completed").scalar()
    avg_relevancy = db.query(func.avg(EvaluationRun.avg_answer_relevancy)).filter(EvaluationRun.status == "completed").scalar()

    # Query counts by retrieval method
    dist_rows = db.query(QueryExecution.retrieval_method, func.count(QueryExecution.id)).group_by(QueryExecution.retrieval_method).all()
    dist = {method: count for method, count in dist_rows}

    return SystemMetricsResponse(
        total_documents=total_docs,
        total_chunks=total_chunks,
        total_queries=total_queries,
        avg_latency_ms=round(float(avg_latency), 2),
        total_tokens_consumed=int(total_tokens),
        estimated_total_cost_usd=round(float(total_cost), 4),
        avg_faithfulness=round(float(avg_faithfulness), 4) if avg_faithfulness is not None else None,
        avg_relevancy=round(float(avg_relevancy), 4) if avg_relevancy is not None else None,
        retrieval_distribution=dist
    )


@router.get("/query-executions/{execution_id}", response_model=QueryExecutionRead)
def get_query_execution_trace(execution_id: str, db: Session = Depends(get_db)):
    """
    Retrieves full step-by-step query execution trace including candidate ranks,
    BM25 and dense scores, fusion results, reranker scores, rewrites, and token usage.
    """
    execution = db.query(QueryExecution).filter(QueryExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Query execution trace not found.")
    return execution
