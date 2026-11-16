"""
Pytest fixtures for database, test client, and test documents.
Uses SQLite in-memory with StaticPool to ensure persistent state across test connections.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.services.sparse_bm25_service import global_bm25_index

# StaticPool ensures that all connections share the same in-memory database
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Provides a clean in-memory database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Reset in-memory BM25 index
    global_bm25_index.chunk_ids = []
    global_bm25_index.chunks_data = []
    global_bm25_index.corpus_tokens = []
    global_bm25_index.bm25 = None
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Provides a FastAPI test client with mocked database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
