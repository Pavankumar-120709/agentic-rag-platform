"""
Unit tests for Reciprocal Rank Fusion (RRF) algorithm and ranking determinism.
"""
from app.services.hybrid_retrieval_service import HybridRetrievalService
from app.schemas.retrieval import RetrievedChunk


def make_chunk(cid: str, dense_rank=None, sparse_rank=None) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=cid,
        document_id="doc-1",
        filename="test.txt",
        chunk_index=0,
        original_text=f"Sample text for {cid}",
        token_count=10,
        dense_rank=dense_rank,
        sparse_rank=sparse_rank
    )


def test_rrf_scoring_and_deduplication():
    # Chunk A is rank 1 in dense, rank 2 in sparse
    # Chunk B is rank 2 in dense, absent in sparse
    # Chunk C is absent in dense, rank 1 in sparse
    dense_results = [make_chunk("A", dense_rank=1), make_chunk("B", dense_rank=2)]
    sparse_results = [make_chunk("C", sparse_rank=1), make_chunk("A", sparse_rank=2)]

    k = 60
    fused = HybridRetrievalService.reciprocal_rank_fusion(dense_results, sparse_results, k=k)

    assert len(fused) == 3
    # Chunk A should have score: 1/(60+1) + 1/(60+2) = 1/61 + 1/62 = 0.016393 + 0.016129 = 0.032522
    chunk_a = next(c for c in fused if c.chunk_id == "A")
    expected_score_a = round(1.0 / 61 + 1.0 / 62, 6)
    assert chunk_a.rrf_score == expected_score_a

    # Chunk A must rank first
    assert fused[0].chunk_id == "A"
    assert chunk_a.dense_rank == 1
    assert chunk_a.sparse_rank == 2


def test_rrf_deterministic_ordering():
    dense_results = [make_chunk(f"C{i}", dense_rank=i) for i in range(1, 6)]
    sparse_results = [make_chunk(f"C{6-i}", sparse_rank=i) for i in range(1, 6)]

    run1 = HybridRetrievalService.reciprocal_rank_fusion(dense_results, sparse_results, k=60)
    run2 = HybridRetrievalService.reciprocal_rank_fusion(dense_results, sparse_results, k=60)

    assert [c.chunk_id for c in run1] == [c.chunk_id for c in run2]
    assert [c.rrf_score for c in run1] == [c.rrf_score for c in run2]


def test_rrf_scale_independence():
    # Raw scores must not skew RRF
    c1_dense = make_chunk("c1", dense_rank=1)
    c1_dense.dense_score = 0.99
    c2_sparse = make_chunk("c2", sparse_rank=1)
    c2_sparse.sparse_score = 1205.4  # High BM25 score

    fused = HybridRetrievalService.reciprocal_rank_fusion([c1_dense], [c2_sparse], k=60)
    # Both appear once at rank 1, so both should receive identical RRF score: 1/(60+1)
    assert fused[0].rrf_score == fused[1].rrf_score
