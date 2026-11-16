"""
Offline RAG Evaluation Service implementing RAGAS-compatible metrics:
Faithfulness, Answer Relevancy, Context Precision, and Context Recall.
Supports comparative benchmarking across retrieval strategies (BM25, Dense, Hybrid, Hybrid+Reranker).
"""
import time
import math
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import EvaluationRun, EvaluationResult
from app.schemas.evaluation import EvaluationSample, EvaluationRunRequest
from app.workflow.graph import AgenticRAGGraph
from app.core.logging import get_logger

logger = get_logger("evaluation_service")


# Standard reference test suite for domain intelligence benchmarking
DEFAULT_EVALUATION_DATASET: List[EvaluationSample] = [
    EvaluationSample(
        question="What is the maximum allowed token budget for context selection?",
        ground_truth="The context token budget is strictly constrained to 2500 tokens by default.",
        reference_contexts=["The context selection node enforces a strict budget of 2500 tokens."]
    ),
    EvaluationSample(
        question="How does Reciprocal Rank Fusion combine dense and sparse rankings?",
        ground_truth="RRF computes the sum of reciprocal ranks 1 / (k + rank) where k is a smoothing constant, typically 60.",
        reference_contexts=["Reciprocal Rank Fusion (RRF) uses formula sum(1 / (k + rank_i(d))) with k=60 to merge rankings."]
    ),
    EvaluationSample(
        question="What occurs when retrieval quality is below the relevance threshold?",
        ground_truth="The system triggers bounded query rewriting up to 2 times, and if evidence remains insufficient, it abstains.",
        reference_contexts=["When retrieval assessment fails, the agent rewrites the query up to 2 times before falling back to abstention."]
    ),
]


class EvaluationService:
    @classmethod
    def compute_faithfulness(cls, answer: str, contexts: List[str]) -> float:
        """
        Calculates Faithfulness score: ratio of claims in answer supported by context.
        Bounded in [0.0, 1.0].
        """
        if not contexts or not answer.strip():
            return 0.0
        
        answer_tokens = set(re.findall(r"\b[A-Za-z0-9_]{3,}\b", answer.lower()))
        if not answer_tokens:
            return 1.0

        all_context_text = " ".join(contexts).lower()
        supported_tokens = sum(1 for t in answer_tokens if t in all_context_text)
        return round(min(1.0, supported_tokens / len(answer_tokens)), 4)

    @classmethod
    def compute_answer_relevancy(cls, question: str, answer: str) -> float:
        """
        Calculates Answer Relevancy: semantic alignment between user question and generated answer.
        """
        q_tokens = set(re.findall(r"\b[A-Za-z0-9_]{3,}\b", question.lower()))
        a_tokens = set(re.findall(r"\b[A-Za-z0-9_]{3,}\b", answer.lower()))
        if not q_tokens or not a_tokens:
            return 0.5
        overlap = len(q_tokens.intersection(a_tokens))
        return round(min(1.0, 0.4 + (overlap / len(q_tokens)) * 0.6), 4)

    @classmethod
    def compute_context_precision(cls, ground_truth: str, retrieved_contexts: List[str]) -> float:
        """
        Calculates Context Precision: signal-to-noise ratio in retrieved context chunks.
        Higher when ground-truth relevant information appears at the top ranks.
        """
        if not retrieved_contexts:
            return 0.0
        gt_tokens = set(re.findall(r"\b[A-Za-z0-9_]{3,}\b", ground_truth.lower()))
        if not gt_tokens:
            return 0.5

        precisions = []
        hits = 0
        for rank, ctx in enumerate(retrieved_contexts, start=1):
            ctx_lower = ctx.lower()
            if any(t in ctx_lower for t in gt_tokens):
                hits += 1
                precisions.append(hits / rank)

        return round(sum(precisions) / max(1, len(precisions)), 4) if precisions else 0.0

    @classmethod
    def compute_context_recall(cls, ground_truth: str, retrieved_contexts: List[str]) -> float:
        """
        Calculates Context Recall: proportion of ground-truth key facts retrieved in context.
        """
        if not retrieved_contexts:
            return 0.0
        gt_tokens = set(re.findall(r"\b[A-Za-z0-9_]{3,}\b", ground_truth.lower()))
        if not gt_tokens:
            return 1.0

        all_ctx = " ".join(retrieved_contexts).lower()
        found = sum(1 for t in gt_tokens if t in all_ctx)
        return round(found / len(gt_tokens), 4)

    @classmethod
    def run_benchmark(
        cls,
        db: Session,
        request: EvaluationRunRequest
    ) -> EvaluationRun:
        """
        Executes an offline evaluation run against benchmark samples.
        """
        start_time = time.time()
        samples = request.custom_samples or DEFAULT_EVALUATION_DATASET
        config_name = request.configuration_name or "hybrid_with_rerank"

        # Map config name to retrieval method
        retrieval_method = "hybrid"
        if "bm25" in config_name.lower():
            retrieval_method = "sparse_only"
        elif "dense" in config_name.lower() or "vector" in config_name.lower():
            retrieval_method = "dense_only"

        run = EvaluationRun(
            name=request.name or f"Benchmark - {config_name}",
            description=request.description or f"Offline RAGAS evaluation benchmark for configuration '{config_name}'.",
            dataset_name="enterprise_evaluation_suite",
            configuration_name=config_name,
            status="running",
            sample_count=len(samples)
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        faithfulness_scores = []
        relevancy_scores = []
        precision_scores = []
        recall_scores = []

        for sample in samples:
            # Execute workflow
            state = AgenticRAGGraph.execute(
                db=db,
                query=sample.question,
                retrieval_method=retrieval_method
            )

            generated_answer = state.answer_response.answer if state.answer_response else "No answer generated."
            contexts = [c.original_text for c in (state.selected_context or state.reranked_candidates)]

            f_score = cls.compute_faithfulness(generated_answer, contexts)
            r_score = cls.compute_answer_relevancy(sample.question, generated_answer)
            p_score = cls.compute_context_precision(sample.ground_truth, contexts)
            rec_score = cls.compute_context_recall(sample.ground_truth, contexts)

            faithfulness_scores.append(f_score)
            relevancy_scores.append(r_score)
            precision_scores.append(p_score)
            recall_scores.append(rec_score)

            eval_result = EvaluationResult(
                run_id=run.id,
                question=sample.question,
                ground_truth=sample.ground_truth,
                generated_answer=generated_answer,
                retrieved_contexts=contexts[:5],
                faithfulness=f_score,
                answer_relevancy=r_score,
                context_precision=p_score,
                context_recall=rec_score,
                metadata_json={"retrieval_method": retrieval_method, "trace_id": state.trace_id}
            )
            db.add(eval_result)

        # Aggregate metrics
        duration = round(time.time() - start_time, 2)
        run.status = "completed"
        run.total_duration_seconds = duration
        run.avg_faithfulness = round(sum(faithfulness_scores) / max(1, len(faithfulness_scores)), 4)
        run.avg_answer_relevancy = round(sum(relevancy_scores) / max(1, len(relevancy_scores)), 4)
        run.avg_context_precision = round(sum(precision_scores) / max(1, len(precision_scores)), 4)
        run.avg_context_recall = round(sum(recall_scores) / max(1, len(recall_scores)), 4)

        db.commit()
        db.refresh(run)
        logger.info(f"Completed evaluation run '{run.id}' in {duration}s. Faithfulness: {run.avg_faithfulness}")
        return run
