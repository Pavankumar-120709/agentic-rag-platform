"""
Unit tests for context token budget enforcement and cost tracking.
"""
from app.services.token_service import TokenService
from app.schemas.retrieval import RetrievedChunk


def test_token_budget_enforcement():
    # Create chunks of 100 tokens each
    chunks = [
        RetrievedChunk(
            chunk_id=f"c-{i}",
            document_id="doc-1",
            filename="data.txt",
            chunk_index=i,
            original_text="Word " * 75,
            token_count=100
        )
        for i in range(10)
    ]

    # Constrain budget to 350 tokens
    selected, total_tokens = TokenService.fit_chunks_within_budget(chunks, max_token_budget=350)
    assert len(selected) == 3
    assert total_tokens == 300
    assert total_tokens <= 350


def test_chunk_deduplication_in_budget():
    chunks = [
        RetrievedChunk(chunk_id="c-dup", document_id="doc-1", filename="a.txt", chunk_index=0, original_text="Text A", token_count=50),
        RetrievedChunk(chunk_id="c-dup", document_id="doc-1", filename="a.txt", chunk_index=0, original_text="Text A", token_count=50),
        RetrievedChunk(chunk_id="c-unique", document_id="doc-1", filename="a.txt", chunk_index=1, original_text="Text B", token_count=50),
    ]

    selected, total_tokens = TokenService.fit_chunks_within_budget(chunks, max_token_budget=500)
    assert len(selected) == 2
    assert total_tokens == 100


def test_cost_calculation():
    prompt_tokens = 1000
    completion_tokens = 500
    cost = TokenService.calculate_cost(prompt_tokens, completion_tokens)
    assert cost > 0.0
    assert isinstance(cost, float)
