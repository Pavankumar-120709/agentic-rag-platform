"""
Unit tests for text extraction, validation, and token-aware chunking.
"""
import pytest
from app.services.chunking_service import ChunkingService
from app.services.token_service import TokenService
from app.core.exceptions import DocumentIngestionError


def test_plain_text_chunking():
    sample_text = (
        "Artificial Intelligence is transforming enterprise software.\n\n"
        "Agentic RAG models combine dense vectors with BM25 keyword search. "
        "Reciprocal Rank Fusion enables robust hybrid rank merging without scale artifacts.\n\n"
        "Cross-encoders score query-document pairs directly for high-precision reranking."
    )
    pages = ChunkingService.extract_text("sample.txt", sample_text.encode("utf-8"))
    assert len(pages) == 1
    assert pages[0].page_number == 1

    chunks = ChunkingService.chunk_document(pages, chunk_size=50, chunk_overlap=10)
    assert len(chunks) >= 2
    for c in chunks:
        assert c.token_count > 0
        assert c.chunk_index >= 0
        assert len(c.text.strip()) > 0


def test_markdown_chunking_with_headers():
    md_content = """# Architecture Overview
This is section 1 discussing system requirements.

## Retrieval Engine
Here we describe pgvector and sparse BM25 indexing.

### Cross Encoder
Detailed reranking logic using transformer models.
"""
    pages = ChunkingService.extract_text("readme.md", md_content.encode("utf-8"))
    assert len(pages) == 1
    chunks = ChunkingService.chunk_document(pages, chunk_size=30, chunk_overlap=5)
    assert len(chunks) >= 2


def test_empty_document_rejection():
    with pytest.raises(DocumentIngestionError):
        ChunkingService.extract_text("empty.txt", b"   ")

    with pytest.raises(DocumentIngestionError):
        ChunkingService.extract_text("empty.pdf", b"")


def test_unsupported_format_rejection():
    with pytest.raises(DocumentIngestionError):
        ChunkingService.extract_text("image.png", b"fake binary data")


def test_token_counting_accuracy():
    text = "The quick brown fox jumps over the lazy dog."
    tokens = TokenService.count_tokens(text)
    assert 8 <= tokens <= 12
