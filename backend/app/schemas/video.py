from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from backend.app.schemas.auto_label import AutoLabelConfig, AutoLabelStatus


class AnalyzeParams(BaseModel):
    model: str = Field("qwen3.5:2b", description="vLLM served model name.")
    frame_prompt: Optional[str] = Field(None, description="Custom prompt for frame descriptions.")
    summary_prompt: Optional[str] = Field(None, description="Custom prompt for video summary.")
    auto_label: AutoLabelConfig = Field(
        default_factory=AutoLabelConfig,
        description="Autonomous auto-labelling configuration.",
    )


class AnalysisResponse(BaseModel):
    caption: str
    frame_captions: list[str]
    frame_count: int
    duration_seconds: float
    device_used: str
    model_id: str


class InitEvent(BaseModel):
    total_frames: int
    video_fps: float
    duration_seconds: float


class FrameEvent(BaseModel):
    index: int
    caption: str
    timestamp_seconds: float = 0.0
    timestamp_end_seconds: Optional[float] = None
    sampled_frame_count: Optional[int] = None
    frame_index_start: Optional[int] = None
    frame_index_end: Optional[int] = None


class SummaryEvent(BaseModel):
    caption: str


class DoneEvent(BaseModel):
    frame_count: int
    duration_seconds: float
    device_used: str
    model_id: str
    video_fps: float = 0.0
    frame_interval: int = 10
    auto_label: AutoLabelStatus = Field(default_factory=AutoLabelStatus)


class ErrorResponse(BaseModel):
    detail: str
    error_type: str
