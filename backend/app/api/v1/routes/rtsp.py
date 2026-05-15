from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.responses import Response, StreamingResponse

from backend.app.schemas.auto_label import AutoLabelConfig, AutoLabelStatus
from backend.app.schemas.rtsp import (
    RTSPErrorResponse,
    RTSPSessionCreateRequest,
    RTSPSessionListResponse,
    RTSPSessionResponse,
)
from backend.app.services.rtsp.manager import rtsp_session_service

router = APIRouter()


@router.post(
    "/sessions",
    response_model=RTSPSessionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": RTSPErrorResponse}},
)
async def create_rtsp_session(
    request: RTSPSessionCreateRequest,
) -> RTSPSessionResponse:
    """Create and start a new RTSP monitoring session."""
    try:
        return rtsp_session_service.create_session(request)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@router.get(
    "/sessions",
    response_model=RTSPSessionListResponse,
)
async def list_rtsp_sessions() -> RTSPSessionListResponse:
    """List RTSP monitoring sessions known to the API."""
    return RTSPSessionListResponse(sessions=rtsp_session_service.list_sessions())


@router.get(
    "/sessions/{session_id}",
    response_model=RTSPSessionResponse,
    responses={404: {"model": RTSPErrorResponse}},
)
async def get_rtsp_session(session_id: str) -> RTSPSessionResponse:
    """Return the current status of one RTSP monitoring session."""
    try:
        return rtsp_session_service.get_session(session_id).snapshot()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete(
    "/sessions/{session_id}",
    response_model=RTSPSessionResponse,
    responses={404: {"model": RTSPErrorResponse}},
)
async def delete_rtsp_session(session_id: str) -> RTSPSessionResponse:
    """Stop and remove one RTSP monitoring session."""
    try:
        return rtsp_session_service.delete_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/sessions/{session_id}/auto-label/start",
    response_model=AutoLabelStatus,
    responses={404: {"model": RTSPErrorResponse}},
)
async def start_rtsp_auto_label(session_id: str, request: AutoLabelConfig) -> AutoLabelStatus:
    """Start autonomous auto-labelling for a live RTSP session."""
    try:
        session = rtsp_session_service.get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return session.start_auto_label(request)


@router.post(
    "/sessions/{session_id}/auto-label/stop",
    response_model=AutoLabelStatus,
    responses={404: {"model": RTSPErrorResponse}},
)
async def stop_rtsp_auto_label(session_id: str) -> AutoLabelStatus:
    """Stop autonomous auto-labelling without stopping RTSP monitoring."""
    try:
        session = rtsp_session_service.get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return session.stop_auto_label(drain=True)


@router.get(
    "/sessions/{session_id}/preview.jpg",
    responses={404: {"model": RTSPErrorResponse}},
)
async def get_rtsp_preview_frame(session_id: str) -> Response:
    """Return the latest RTSP preview frame as a single JPEG."""
    try:
        session = rtsp_session_service.get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    jpeg = session.get_preview_jpeg()
    if jpeg is None:
        raise HTTPException(status_code=404, detail="No preview frame is available yet.")

    return Response(content=jpeg, media_type="image/jpeg")


@router.get(
    "/sessions/{session_id}/preview.mjpeg",
    responses={404: {"model": RTSPErrorResponse}},
)
async def get_rtsp_preview_stream(session_id: str) -> StreamingResponse:
    """Return the live RTSP preview as an MJPEG stream for the web UI."""
    try:
        session = rtsp_session_service.get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    boundary = "frame"

    async def event_stream():
        while True:
            jpeg = session.get_preview_jpeg()
            status_snapshot = session.snapshot().status
            if jpeg is not None:
                yield (
                    f"--{boundary}\r\n"
                    "Content-Type: image/jpeg\r\n"
                    f"Content-Length: {len(jpeg)}\r\n\r\n"
                ).encode("utf-8") + jpeg + b"\r\n"
            if status_snapshot == "stopped":
                break
            await asyncio.sleep(0.1)

    return StreamingResponse(
        event_stream(),
        media_type=f"multipart/x-mixed-replace; boundary={boundary}",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.websocket("/sessions/{session_id}/events")
async def rtsp_session_events(websocket: WebSocket, session_id: str) -> None:
    """Push real-time RTSP session events to the client via WebSocket."""
    await websocket.accept()

    try:
        _session, subscriber_id, queue = await rtsp_session_service.subscribe(session_id)
    except KeyError:
        await websocket.send_json(
            {
                "event": "error",
                "session_id": session_id,
                "emitted_at": None,
                "data": {"message": "Unknown RTSP session."},
            }
        )
        await websocket.close(code=4404)
        return

    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event)
            if event.get("event") == "stopped":
                break
    except WebSocketDisconnect:
        pass
    finally:
        rtsp_session_service.unsubscribe(session_id, subscriber_id)
