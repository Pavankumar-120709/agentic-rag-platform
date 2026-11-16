"""
Unit tests for deterministic citation validation and quote verification.
"""
from app.workflow.state import AgenticRAGState
from app.workflow.nodes import WorkflowNodes
from app.schemas.retrieval import RetrievedChunk
from app.schemas.chat import AnswerResponse, Citation


def test_valid_citation():
    chunk = RetrievedChunk(
        chunk_id="chunk-123",
        document_id="doc-abc",
        filename="system_spec.txt",
        chunk_index=0,
        original_text="The system architecture utilizes PostgreSQL with pgvector for high-dimensional vector storage.",
        token_count=15
    )

    state = AgenticRAGState(
        trace_id="t1",
        query="What database is used?",
        original_query="What database is used?",
        selected_context=[chunk],
        answer_response=AnswerResponse(
            answer="The system relies on PostgreSQL with pgvector for vector storage.",
            citations=[
                Citation(
                    document_id="doc-abc",
                    filename="system_spec.txt",
                    chunk_id="chunk-123",
                    page_number=1,
                    quoted_text="PostgreSQL with pgvector for high-dimensional vector storage"
                )
            ],
            confidence_label="supported",
            evidence_summary="Verified",
            warnings=[]
        )
    )

    state = WorkflowNodes.validate_citations(state, db=None)
    assert state.citation_valid is True
    assert len(state.validation_errors) == 0


def test_invalid_chunk_id_rejection():
    chunk = RetrievedChunk(
        chunk_id="chunk-real",
        document_id="doc-1",
        filename="real.txt",
        chunk_index=0,
        original_text="Valid document content here.",
        token_count=5
    )

    state = AgenticRAGState(
        trace_id="t2",
        query="Query",
        original_query="Query",
        selected_context=[chunk],
        answer_response=AnswerResponse(
            answer="Some answer.",
            citations=[
                Citation(
                    document_id="doc-1",
                    filename="real.txt",
                    chunk_id="chunk-fake-999",  # Hallucinated ID
                    page_number=1,
                    quoted_text="Valid document content here."
                )
            ],
            confidence_label="supported",
            evidence_summary="None",
            warnings=[]
        )
    )

    state = WorkflowNodes.validate_citations(state, db=None)
    assert state.citation_valid is False
    assert any("unretrieved chunk_id" in err for err in state.validation_errors)


def test_fabricated_quote_rejection():
    chunk = RetrievedChunk(
        chunk_id="chunk-real",
        document_id="doc-1",
        filename="real.txt",
        chunk_index=0,
        original_text="The API latency is bounded to 50 milliseconds under standard load.",
        token_count=10
    )

    state = AgenticRAGState(
        trace_id="t3",
        query="What is the throughput?",
        original_query="What is the throughput?",
        selected_context=[chunk],
        answer_response=AnswerResponse(
            answer="Throughput is 50,000 requests per second.",
            citations=[
                Citation(
                    document_id="doc-1",
                    filename="real.txt",
                    chunk_id="chunk-real",
                    page_number=1,
                    quoted_text="Throughput is 50,000 requests per second"  # Fabricated quote not in chunk
                )
            ],
            confidence_label="supported",
            evidence_summary="None",
            warnings=[]
        )
    )

    state = WorkflowNodes.validate_citations(state, db=None)
    assert state.citation_valid is False
    assert any("quoted_text not found" in err for err in state.validation_errors)
