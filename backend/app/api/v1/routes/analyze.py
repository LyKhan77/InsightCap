from __future__ import annotations

import os
import tempfile
from pathlib import Path
from contextlib import asynccontextmanager, contextmanager
from typing import Annotated, Optional

from fastapi import APIRouter, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response, StreamingResponse

from backend.app.schemas.auto_label import AutoLabelConfig
from backend.app.schemas.video import AnalysisResponse, AnalyzeParams
from backend.app.services.auto_label import DATASET_ROOT
from backend.app.services.video_analysis import AnalysisService

router = APIRouter()
_service = AnalysisService()

_ALLOWED_CONTENT_TYPES = {
    "video/mp4", "video/avi", "video/quicktime", "video/x-msvideo",
    "video/x-matroska", "video/webm", "video/mpeg", "application/octet-stream",
}
_ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".mpeg", ".mpg"}


def _validate_video(file: UploadFile) -> None:
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(_ALLOWED_EXTENSIONS)}",
        )


@contextmanager
def _temp_video(file: UploadFile):
    """Save UploadFile to a temp path, yield path, then delete."""
    ext = os.path.splitext(file.filename or ".mp4")[1].lower() or ".mp4"
    fd, path = tempfile.mkstemp(suffix=ext)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(file.file.read())
        yield path
    finally:
        if os.path.exists(path):
            os.unlink(path)




@router.get("/auto-label/overlay")
async def get_auto_label_overlay(path: str = Query(...)) -> Response:
    """Serve a generated annotated overlay image from the auto-label dataset root."""
    root = DATASET_ROOT.resolve()
    target = Path(path).resolve()
    if root != target and root not in target.parents:
        raise HTTPException(status_code=403, detail="Overlay path is outside the auto-label dataset root.")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Auto-label overlay is not available.")
    return Response(content=target.read_bytes(), media_type="image/jpeg")

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    file: UploadFile,
    model: Annotated[str, Form()] = "qwen3.5:2b",
    frame_prompt: Annotated[Optional[str], Form()] = None,
    summary_prompt: Annotated[Optional[str], Form()] = None,
    auto_label_enabled: Annotated[bool, Form()] = False,
    auto_label_prompt: Annotated[str, Form()] = "",
    auto_label_duration_minutes: Annotated[float, Form()] = 5.0,
    auto_label_confidence: Annotated[float, Form()] = 0.25,
    auto_label_model: Annotated[str, Form()] = "yoloe-26s-seg.pt",
) -> AnalysisResponse:
    """Upload a video file and receive a full caption result as JSON."""
    _validate_video(file)
    params = AnalyzeParams(
        model=model,
        frame_prompt=frame_prompt,
        summary_prompt=summary_prompt,
        auto_label=AutoLabelConfig(
            enabled=auto_label_enabled,
            prompt=auto_label_prompt,
            duration_minutes=auto_label_duration_minutes,
            confidence=auto_label_confidence,
            model=auto_label_model,
        ),
    )
    try:
        with _temp_video(file) as path:
            return await _service.run(path, params)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/analyze/stream")
async def analyze_stream(
    file: UploadFile,
    model: Annotated[str, Form()] = "qwen3.5:2b",
    frame_prompt: Annotated[Optional[str], Form()] = None,
    summary_prompt: Annotated[Optional[str], Form()] = None,
    auto_label_enabled: Annotated[bool, Form()] = False,
    auto_label_prompt: Annotated[str, Form()] = "",
    auto_label_duration_minutes: Annotated[float, Form()] = 5.0,
    auto_label_confidence: Annotated[float, Form()] = 0.25,
    auto_label_model: Annotated[str, Form()] = "yoloe-26s-seg.pt",
) -> StreamingResponse:
    """Upload a video file and receive captions as Server-Sent Events.

    Events are emitted in real-time as each frame is captioned.
    """
    _validate_video(file)
    params = AnalyzeParams(
        model=model,
        frame_prompt=frame_prompt,
        summary_prompt=summary_prompt,
        auto_label=AutoLabelConfig(
            enabled=auto_label_enabled,
            prompt=auto_label_prompt,
            duration_minutes=auto_label_duration_minutes,
            confidence=auto_label_confidence,
            model=auto_label_model,
        ),
    )

    # Save the file to temp before streaming (UploadFile can't be read in a background thread)
    ext = os.path.splitext(file.filename or ".mp4")[1].lower() or ".mp4"
    fd, path = tempfile.mkstemp(suffix=ext)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(file.file.read())
    except Exception as exc:
        if os.path.exists(path):
            os.unlink(path)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    async def event_stream():
        try:
            async for event in _service.run_stream(path, params):
                yield event
        finally:
            if os.path.exists(path):
                os.unlink(path)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
