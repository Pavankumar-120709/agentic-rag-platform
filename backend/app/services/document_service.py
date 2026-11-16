"""
Document Ingestion, Lifecycle Management, and Ingestion Persistence Service.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.exceptions import (
    DocumentIngestionError,
    DuplicateDocumentError
)
from app.core.security import compute_sha256, sanitize_text
from app.db.models import Document, DocumentChunk
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.sparse_bm25_service import global_bm25_index
from app.services.hybrid_retrieval_service import HybridRetrievalService
from app.core.logging import get_logger

logger = get_logger("document_service")


class DocumentService:
    @classmethod
    def ingest_document(
        cls,
        db: Session,
        filename: str,
        content: bytes,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> Document:
        """
        Ingests, parses, validates, chunks, embeds, and persists a document.
        """
        # 1. Enforce file size limit
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise DocumentIngestionError(
                f"File size ({len(content)} bytes) exceeds the maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
            )

        # 2. Duplicate detection via SHA-256
        content_hash = compute_sha256(content)
        existing = db.query(Document).filter(Document.content_hash == content_hash).first()
        if existing:
            raise DuplicateDocumentError(
                f"An identical document with SHA-256 hash '{content_hash}' already exists ('{existing.filename}').",
                details={"existing_document_id": existing.id, "filename": existing.filename}
            )

        # 3. Create document record in 'processing' state
        ext = filename.lower().split(".")[-1] if "." in filename else "unknown"
        doc = Document(
            filename=filename,
            file_type=ext,
            file_size_bytes=len(content),
            content_hash=content_hash,
            status="processing",
            metadata_json={"original_filename": filename, "extension": ext}
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        try:
            # 4. Extract text
            pages = ChunkingService.extract_text(filename, content)
            
            # 5. Token-aware chunking
            effective_chunk_size = chunk_size or settings.DEFAULT_CHUNK_SIZE
            effective_overlap = chunk_overlap or settings.DEFAULT_CHUNK_OVERLAP
            raw_chunks = ChunkingService.chunk_document(
                pages,
                chunk_size=effective_chunk_size,
                chunk_overlap=effective_overlap
            )

            if not raw_chunks:
                raise DocumentIngestionError(f"No valid text chunks could be extracted from '{filename}'.")

            # 6. Generate embeddings in batches
            chunk_texts = [sanitize_text(rc.text) for rc in raw_chunks]
            embeddings = EmbeddingService.get_embeddings_batch(chunk_texts)

            # 7. Persist chunks
            total_tokens = 0
            created_chunks: List[DocumentChunk] = []
            for rc, emb in zip(raw_chunks, embeddings):
                total_tokens += rc.token_count
                chunk_obj = DocumentChunk(
                    document_id=doc.id,
                    filename=doc.filename,
                    chunk_index=rc.chunk_index,
                    page_number=rc.page_number,
                    original_text=rc.text,
                    token_count=rc.token_count,
                    embedding=emb,
                    metadata_json=rc.metadata
                )
                db.add(chunk_obj)
                created_chunks.append(chunk_obj)

            # 8. Update document status to indexed
            doc.status = "indexed"
            doc.total_chunks = len(created_chunks)
            doc.total_tokens = total_tokens
            db.commit()
            db.refresh(doc)

            # 9. Sync BM25 in-memory index
            HybridRetrievalService.sync_bm25_index(db)
            logger.info(f"Successfully indexed document '{filename}' with {doc.total_chunks} chunks.")
            return doc

        except Exception as e:
            db.rollback()
            doc.status = "failed"
            doc.error_message = str(e)
            db.commit()
            logger.error(f"Failed to ingest document '{filename}': {str(e)}")
            raise

    @classmethod
    def get_document(cls, db: Session, document_id: str) -> Optional[Document]:
        return db.query(Document).filter(Document.id == document_id).first()

    @classmethod
    def list_documents(cls, db: Session) -> List[Document]:
        return db.query(Document).order_by(Document.created_at.desc()).all()

    @classmethod
    def delete_document(cls, db: Session, document_id: str) -> bool:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return False
        db.delete(doc)
        db.commit()
        # Resync BM25 index after deletion
        HybridRetrievalService.sync_bm25_index(db)
        return True
