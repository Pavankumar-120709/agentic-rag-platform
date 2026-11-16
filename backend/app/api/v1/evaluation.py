"""
FastAPI router for Offline Evaluation and RAGAS Benchmarking.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import EvaluationRun, EvaluationResult
from app.schemas.evaluation import EvaluationRunRequest, EvaluationRunRead, EvaluationResultRead
from app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


@router.post("/run", response_model=EvaluationRunRead, status_code=status.HTTP_201_CREATED)
def trigger_evaluation_run(request: EvaluationRunRequest, db: Session = Depends(get_db)):
    """
    Executes an offline RAGAS-compatible evaluation run.
    Computes Faithfulness, Answer Relevancy, Context Precision, and Context Recall.
    """
    try:
        run = EvaluationService.run_benchmark(db, request)
        return run
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation execution failed: {str(e)}"
        )


@router.get("/runs", response_model=List[EvaluationRunRead])
def list_evaluation_runs(db: Session = Depends(get_db)):
    """Lists historical evaluation runs across all retrieval configurations."""
    runs = db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).all()
    return runs


@router.get("/runs/{run_id}", response_model=EvaluationRunRead)
def get_evaluation_run(run_id: str, db: Session = Depends(get_db)):
    """Retrieves specific evaluation run with per-sample scores and retrieved contexts."""
    run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found.")
    return run
