from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyzeParams(BaseModel):
    model: str = Field("qwen3.5:0.8b", description="Ollama model name.")


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


class SummaryEvent(BaseModel):
    caption: str


class DoneEvent(BaseModel):
    frame_count: int
    duration_seconds: float
    device_used: str
    model_id: str
    video_fps: float = 0.0
    frame_interval: int = 10


class ErrorResponse(BaseModel):
    detail: str
    error_type: str
