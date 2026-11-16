"""
Application configuration using Pydantic Settings.
Centralizes all environment variables, bounded agent parameters, and retrieval settings.
"""
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core Application
    ENVIRONMENT: str = "development"
    APP_NAME: str = "Agentic RAG Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Security & Networking
    SECRET_KEY: str = "change-this-in-production-to-a-secure-random-32-byte-hex"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    RATE_LIMIT_PER_MINUTE: int = 60
    MAX_UPLOAD_SIZE_MB: int = 25

    # Storage & Database
    DATABASE_URL: str = "sqlite:///./rag_local.db"
    
    # Vector Engine
    VECTOR_DIMENSION: int = 384
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_BATCH_SIZE: int = 32

    # Retrieval & RRF
    RERANKER_MODEL_NAME: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RETRIEVAL_TOP_K: int = 10
    RERANK_TOP_K: int = 5
    RRF_K: int = 60
    MIN_RELEVANCE_SCORE_THRESHOLD: float = 0.35

    # Ingestion & Chunking
    DEFAULT_CHUNK_SIZE: int = 512
    DEFAULT_CHUNK_OVERLAP: int = 64

    # LLM & Generation
    LLM_PROVIDER: str = "mock"  # mock, openai, anthropic, google
    LLM_MODEL: str = "gpt-4o-mini"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # Bounded Agentic Constraints
    MAX_QUERY_REWRITES: int = 2
    MAX_GENERATION_ATTEMPTS: int = 2
    CONTEXT_TOKEN_BUDGET: int = 2500

    # Pricing (per 1k tokens USD estimates for token cost tracking)
    INPUT_TOKEN_PRICE_PER_1K: float = 0.00015
    OUTPUT_TOKEN_PRICE_PER_1K: float = 0.00060


settings = Settings()
