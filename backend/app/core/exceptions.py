"""
Domain-specific exceptions for Document Ingestion, Retrieval, Agent, and Evaluation errors.
"""
from typing import Optional, Dict, Any


class RAGException(Exception):
    """Base exception for all RAG system failures."""
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class DocumentIngestionError(RAGException):
    """Raised when parsing, validating, or chunking a document fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=400, details=details)


class DuplicateDocumentError(RAGException):
    """Raised when an identical document hash already exists in storage."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=409, details=details)


class RetrievalError(RAGException):
    """Raised when dense, sparse, or hybrid retrieval fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=502, details=details)


class CitationValidationError(RAGException):
    """Raised when generated citations are ungrounded or fabricated."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=422, details=details)


class FaithfulnessValidationError(RAGException):
    """Raised when an answer contains hallucinated or unfaithful claims."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=422, details=details)


class LLMProviderError(RAGException):
    """Raised when an external LLM provider times out or returns non-retryable errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=504, details=details)
