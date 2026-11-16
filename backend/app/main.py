"""
FastAPI application entrypoint for the Agentic RAG Platform.
"""
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import RAGException
from app.db.session import init_db
from app.api.v1.router import api_v1_router

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler initializing DB and pre-warming models."""
    logger.info("Initializing database schemas...")
    init_db()
    logger.info("Application startup complete.")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-grade Agentic RAG platform with Hybrid BM25/Vector retrieval, RRF, Cross-Encoder reranking, bounded LangGraph orchestration, and deterministic citation verification.",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Logs incoming request method, path, and duration."""
    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)")
    return response


@app.exception_handler(RAGException)
async def rag_exception_handler(request: Request, exc: RAGException):
    """Custom exception handler for domain errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.__class__.__name__, "message": exc.message, "details": exc.details}
    )


# Register API v1 routes
app.include_router(api_v1_router)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
        "health": "/api/health"
    }
