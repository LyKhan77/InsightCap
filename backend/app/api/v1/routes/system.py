from __future__ import annotations

import requests
from fastapi import APIRouter

from backend.core.config import InferenceConfig
from backend.core.device import detect_device

router = APIRouter()


@router.get("/health", tags=["system"])
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


@router.get("/", tags=["system"])
async def root() -> dict:
    return {"name": "InsightCap API", "version": "2.0.0", "docs": "/docs"}
