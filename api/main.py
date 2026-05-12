from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

from insightcap.config import InferenceConfig
from insightcap.device import detect_device
from api.routes.analyze import router as analyze_router
from api.routes.rtsp import router as rtsp_router
from api.rtsp_service import rtsp_session_service

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

app.include_router(analyze_router, prefix="/api/v1", tags=["analyze"])
app.include_router(rtsp_router, prefix="/api/v1/rtsp", tags=["rtsp"])


@app.get("/health", tags=["system"])
async def health() -> dict:
    """Return API health, compute device, and vLLM reachability."""
    config = InferenceConfig()
    base_url = config.vllm_base_url.rstrip("/")
    server_url = base_url[:-3] if base_url.endswith("/v1") else base_url
    vllm_status = {"status": "ok", "base_url": config.vllm_base_url}
    try:
        requests.get(f"{server_url}/health", timeout=2).raise_for_status()
    except Exception as exc:
        vllm_status = {
            "status": "unreachable",
            "base_url": config.vllm_base_url,
            "error": str(exc),
        }
    return {
        "status": "ok",
        "device": detect_device(),
        "backend": config.backend,
        "vllm": vllm_status,
    }


@app.get("/", tags=["system"])
async def root() -> dict:
    return {"name": "InsightCap API", "version": "2.0.0", "docs": "/docs"}


@app.on_event("shutdown")
async def shutdown_rtsp_sessions() -> None:
    """Ensure background RTSP worker threads are asked to stop."""
    rtsp_session_service.shutdown()
