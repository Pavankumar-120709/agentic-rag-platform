"""
Unit tests for bounded query rewriting and intent preservation.
"""
from app.workflow.state import AgenticRAGState
from app.workflow.nodes import WorkflowNodes


def test_bounded_query_rewriting():
    state = AgenticRAGState(
        trace_id="trace-rewrite",
        query="what is the default chunk overlap size?",
        original_query="what is the default chunk overlap size?",
        max_rewrites=2
    )

    # First rewrite
    state = WorkflowNodes.rewrite_query(state, db=None)
    assert state.rewrite_count == 1
    assert len(state.rewritten_queries) == 1
    first_rewrite = state.query
    assert first_rewrite != state.original_query
    assert "default chunk overlap size" in first_rewrite

    # Second rewrite
    state = WorkflowNodes.rewrite_query(state, db=None)
    assert state.rewrite_count == 2
    assert len(state.rewritten_queries) == 2
    second_rewrite = state.query
    assert second_rewrite != first_rewrite


def test_avoid_duplicate_rewrites():
    state = AgenticRAGState(
        trace_id="trace-dup",
        query="PostgreSQL vector",
        original_query="PostgreSQL vector",
        max_rewrites=2
    )
    state = WorkflowNodes.rewrite_query(state, db=None)
    r1 = state.query
    state = WorkflowNodes.rewrite_query(state, db=None)
    r2 = state.query
    assert r1 != r2
