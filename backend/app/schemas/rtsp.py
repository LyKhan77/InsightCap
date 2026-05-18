from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from backend.app.schemas.auto_label import AutoLabelConfig, AutoLabelStatus


class RTSPSessionCreateRequest(BaseModel):
    rtsp_url: str = Field(..., description="RTSP camera URL.")
    model: str = Field("qwen3.5:2b", description="vLLM served model name.")
    sample_every_seconds: float = Field(
        1.0,
        gt=0,
        le=60,
        description="Minimum seconds between sampled live frames.",
    )
    session_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Optional display name for the RTSP session.",
    )
    frame_prompt: Optional[str] = Field(
        default=None,
        description="Custom prompt for live frame descriptions.",
    )
    auto_label: AutoLabelConfig = Field(
        default_factory=AutoLabelConfig,
        description="Autonomous auto-labelling configuration.",
    )


class RTSPSessionResponse(BaseModel):
    session_id: str
    session_name: str
    status: str
    source: str
    model_id: str
    sample_every_seconds: float
    started_at: Optional[datetime] = None
    last_event_at: Optional[datetime] = None
    last_caption: Optional[str] = None
    captions_emitted: int = 0
    reconnect_count: int = 0
    lag_ms: Optional[float] = None
    last_error: Optional[str] = None
    auto_label: AutoLabelStatus = Field(default_factory=AutoLabelStatus)


class RTSPSessionListResponse(BaseModel):
    sessions: list[RTSPSessionResponse]


class RTSPEvent(BaseModel):
    event: str
    session_id: str
    emitted_at: datetime
    data: dict[str, Any]


class RTSPErrorResponse(BaseModel):
    detail: str
    error_type: str
