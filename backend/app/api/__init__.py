"""API router aggregator."""

from fastapi import APIRouter

from backend.app.api.plan import router as plan_router
from backend.app.api.providers import router as providers_router
from backend.app.api.scan import router as scan_router
from backend.app.api.undo import router as undo_router

api_router = APIRouter()
api_router.include_router(scan_router)
api_router.include_router(providers_router)
api_router.include_router(plan_router)
api_router.include_router(undo_router)

__all__ = ["api_router"]
