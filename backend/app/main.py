from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1.router import api_router
from backend.app.api.v1.routes.system import router as system_router
from backend.app.services.rtsp.manager import rtsp_session_service

app = FastAPI(
    title="InsightCap API",
    description="Video understanding and captioning via Qwen3.5:0.8b + vLLM.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system_router)
app.include_router(api_router)


@app.on_event("shutdown")
async def shutdown_rtsp_sessions() -> None:
    """Ensure background RTSP worker threads are asked to stop."""
    rtsp_session_service.shutdown()
