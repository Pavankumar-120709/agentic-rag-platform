"""
Agentic RAG Orchestration Graph.
Executes the bounded 15-node workflow with explicit termination criteria,
query rewrite loops, citation verification, and automated fallbacks.
"""
import time
import uuid
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.workflow.state import AgenticRAGState
from app.workflow.nodes import WorkflowNodes
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("workflow_graph")


class AgenticRAGGraph:
    """
    Bounded state machine orchestrating the Agentic RAG workflow.
    Guarantees termination in at most (max_rewrites + 1) retrieval iterations
    and (max_generations) generation iterations.
    """

    @classmethod
    def execute(
        cls,
        db: Session,
        query: str,
        conversation_id: str = None,
        retrieval_method: str = "hybrid",
        max_rewrites: int = None,
        context_token_budget: int = None
    ) -> AgenticRAGState:
        start_time = time.time()
        trace_id = f"trace-{uuid.uuid4().hex[:12]}"

        state = AgenticRAGState(
            trace_id=trace_id,
            query=query,
            original_query=query,
            conversation_id=conversation_id,
            retrieval_method=retrieval_method or "hybrid",
            max_rewrites=max_rewrites if max_rewrites is not None else settings.MAX_QUERY_REWRITES,
            max_generations=settings.MAX_GENERATION_ATTEMPTS,
            context_token_budget=context_token_budget or settings.CONTEXT_TOKEN_BUDGET
        )

        logger.info(f"Starting Agentic RAG execution. Trace ID: {trace_id}, Query: '{query}'")

        # 1. Classify Query
        state = WorkflowNodes.classify_query(state, db)
        if state.final_status == "fallback":
            state = WorkflowNodes.fallback_answer(state, db)
            state.latency_ms = round((time.time() - start_time) * 1000, 2)
            return state

        # 2. Initial Retrieval, Fusion & Reranking
        state = WorkflowNodes.retrieve_hybrid(state, db)
        state = WorkflowNodes.fuse_results(state, db)
        state = WorkflowNodes.rerank_documents(state, db)
        state = WorkflowNodes.assess_retrieval(state, db)

        # 3. Bounded Query Rewriting Loop
        while not state.evidence_sufficient and state.rewrite_count < state.max_rewrites:
            state = WorkflowNodes.rewrite_query(state, db)
            state = WorkflowNodes.retrieve_again(state, db)
            state = WorkflowNodes.assess_retrieval(state, db)

        # 4. Check if evidence is still insufficient after rewrites
        if not state.evidence_sufficient or not state.reranked_candidates:
            state.fallback_reason = "insufficient_evidence"
            state = WorkflowNodes.fallback_answer(state, db)
            state.latency_ms = round((time.time() - start_time) * 1000, 2)
            return state

        # 5. Context Selection (Token Budgeted & Deduplicated)
        state = WorkflowNodes.select_context(state, db)

        # 6. Answer Generation
        state = WorkflowNodes.generate_answer(state, db)
        state = WorkflowNodes.validate_output(state, db)
        state = WorkflowNodes.validate_citations(state, db)
        state = WorkflowNodes.evaluate_faithfulness(state, db)

        # 7. Bounded Regeneration Loop (Max 1 retry)
        if (not state.faithfulness_passed or not state.citation_valid or not state.output_valid) and (state.generation_attempts < state.max_generations):
            state = WorkflowNodes.regenerate_answer(state, db)

        # 8. Final Decision: Finalize or Fallback
        if state.output_valid and state.citation_valid and state.faithfulness_passed:
            state = WorkflowNodes.finalize_answer(state, db)
        else:
            state.fallback_reason = "verification_failure"
            state = WorkflowNodes.fallback_answer(state, db)

        state.latency_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Completed execution. Status: {state.final_status}, Latency: {state.latency_ms}ms")
        return state
