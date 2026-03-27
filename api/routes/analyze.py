from __future__ import annotations

import os
import tempfile
from contextlib import asynccontextmanager, contextmanager
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from api.schemas import AnalysisResponse, AnalyzeParams
from api.service import AnalysisService

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


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    file: UploadFile,
    model: Annotated[str, Form()] = "qwen3.5:0.8b",
) -> AnalysisResponse:
    """Upload a video file and receive a full caption result as JSON."""
    _validate_video(file)
    params = AnalyzeParams(model=model)
    try:
        with _temp_video(file) as path:
            return await _service.run(path, params)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/analyze/stream")
async def analyze_stream(
    file: UploadFile,
    model: Annotated[str, Form()] = "qwen3.5:0.8b",
) -> StreamingResponse:
    """Upload a video file and receive captions as Server-Sent Events.

    Events are emitted in real-time as each frame is captioned.
    """
    _validate_video(file)
    params = AnalyzeParams(model=model)

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
