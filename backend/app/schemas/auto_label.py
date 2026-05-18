from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class AutoLabelConfig(BaseModel):
    enabled: bool = Field(False, description="Whether autonomous auto-labelling is enabled.")
    prompt: str = Field("", description="Comma or newline separated object labels to detect.")
    schedule_mode: Literal["duration", "automatic"] = Field(
        "duration",
        description="Auto-labelling scheduler mode: fixed duration or automatic until manually stopped.",
    )
    duration_minutes: float = Field(
        5.0,
        gt=0,
        le=1440,
        description="Maximum duration for autonomous labelling.",
    )
    confidence: float = Field(
        0.25,
        ge=0,
        le=1,
        description="Detector confidence threshold.",
    )
    model: str = Field("yoloe-26s-seg.pt", description="YOLOE detector model.")


class AutoLabelStatus(BaseModel):
    status: str = "idle"
    dataset_path: Optional[str] = None
    latest_overlay_path: Optional[str] = None
    frames_labelled: int = 0
    frames_dropped: int = 0
    chunks_enqueued: int = 0
    remaining_seconds: Optional[float] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    last_error: Optional[str] = None
