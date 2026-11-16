"""
Master API router bundling documents, chat, evaluation, metrics, and health routers.
"""
from fastapi import APIRouter
from app.api.v1.documents import router as documents_router
from app.api.v1.chat import router as chat_router
from app.api.v1.evaluation import router as evaluation_router
from app.api.v1.observability import router as observability_router
from app.api.v1.health import router as health_router

api_v1_router = APIRouter(prefix="/api")

api_v1_router.include_router(health_router)
api_v1_router.include_router(documents_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(evaluation_router)
api_v1_router.include_router(observability_router)
