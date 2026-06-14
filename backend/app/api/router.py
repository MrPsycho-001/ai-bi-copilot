from fastapi import APIRouter
from app.api.endpoints import health, datasets, chat

api_router = APIRouter()

api_router.include_router(health.router, tags=["System Health"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["Dataset Management"])
# We removed the sub-prefix here to let the endpoint file handle it explicitly
api_router.include_router(chat.router, tags=["Agentic AI Chat Engine"])
