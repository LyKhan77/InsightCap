from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.v1.routes.analyze import router as analyze_router
from backend.app.api.v1.routes.rtsp import router as rtsp_router

api_router = APIRouter()
api_router.include_router(analyze_router, prefix="/api/v1", tags=["analyze"])
api_router.include_router(rtsp_router, prefix="/api/v1/rtsp", tags=["rtsp"])
