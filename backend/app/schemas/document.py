"""
Pydantic schemas for Document Ingestion and Chunk inspection.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class DocumentChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    filename: str
    chunk_index: int
    page_number: Optional[int] = None
    original_text: str
    token_count: int
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    file_type: str
    file_size_bytes: int
    content_hash: str
    status: str
    total_chunks: int
    total_tokens: int
    error_message: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class DocumentDetail(DocumentRead):
    chunks: List[DocumentChunkRead] = Field(default_factory=list)


class DocumentStatusResponse(BaseModel):
    id: str
    filename: str
    status: str
    total_chunks: int
    total_tokens: int
    error_message: Optional[str] = None
