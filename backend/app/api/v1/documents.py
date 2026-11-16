"""
FastAPI router for Document Ingestion, Inspection, Status, and Deletion.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.document_service import DocumentService
from app.schemas.document import DocumentRead, DocumentDetail, DocumentStatusResponse
from app.core.exceptions import DuplicateDocumentError, DocumentIngestionError

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: Optional[int] = Form(None),
    chunk_overlap: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload and index a PDF, TXT, or Markdown document.
    Executes parsing, token-aware chunking, batch embeddings, pgvector persistence, and BM25 indexing.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename must be provided.")

    try:
        content = await file.read()
        doc = DocumentService.ingest_document(
            db=db,
            filename=file.filename,
            content=content,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        return doc
    except DuplicateDocumentError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    except DocumentIngestionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ingestion failed: {str(e)}")


@router.get("", response_model=List[DocumentRead])
def list_documents(db: Session = Depends(get_db)):
    """Lists all registered documents with processing status and chunk statistics."""
    return DocumentService.list_documents(db)


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Retrieves document metadata along with all child chunk records and token counts."""
    doc = DocumentService.get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return doc


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def get_document_status(document_id: str, db: Session = Depends(get_db)):
    """Retrieves real-time processing status of an ingested document."""
    doc = DocumentService.get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return DocumentStatusResponse(
        id=doc.id,
        filename=doc.filename,
        status=doc.status,
        total_chunks=doc.total_chunks,
        total_tokens=doc.total_tokens,
        error_message=doc.error_message
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Deletes a document, cascading chunk deletion and synchronizing BM25 index."""
    deleted = DocumentService.delete_document(db, document_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return None
