from __future__ import annotations

import asyncio
import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

import cv2

from insightcap.config import InferenceConfig
from insightcap.inference.factory import get_backend
from insightcap.prompt.builder import PromptBuilder
from insightcap.video.live_reader import LiveStreamReader

from api.rtsp_schemas import RTSPSessionCreateRequest, RTSPSessionResponse


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _mask_rtsp_url(url: str) -> str:
    parts = urlsplit(url)
    if not parts.scheme:
        return url
    hostname = parts.hostname or ""
    port = f":{parts.port}" if parts.port else ""
    if parts.username or parts.password:
        netloc = f"***@{hostname}{port}"
    else:
        netloc = f"{hostname}{port}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def _default_session_name(url: str) -> str:
    host = urlsplit(url).hostname or "rtsp-camera"
    return host


class RtspSession:
    """Owns one RTSP monitoring session and its worker thread."""

    _HEARTBEAT_SECONDS = 5.0
    _RECONNECT_DELAY_SECONDS = 2.0
    _IDLE_WAIT_SECONDS = 0.02
    _RECENT_EVENTS_MAX = 32
    _RECENT_CAPTIONS_MAX = 8
    _SUBSCRIBER_QUEUE_MAX = 32
    _PREVIEW_INTERVAL_SECONDS = 0.1
    _PREVIEW_MAX_WIDTH = 960
    _PREVIEW_JPEG_QUALITY = 70

    def __init__(self, session_id: str, request: RTSPSessionCreateRequest) -> None:
        self.session_id = session_id
        self.rtsp_url = request.rtsp_url
        self.source = _mask_rtsp_url(request.rtsp_url)
        self.session_name = request.session_name or _default_session_name(request.rtsp_url)
        self.model_id = request.model
        self.sample_every_seconds = request.sample_every_seconds

        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name=f"rtsp-session-{session_id}",
            daemon=True,
        )
        self._subscribers: dict[str, tuple[asyncio.AbstractEventLoop, asyncio.Queue]] = {}
        self._recent_events: deque[dict[str, Any]] = deque(maxlen=self._RECENT_EVENTS_MAX)
        self._recent_captions: deque[str] = deque(maxlen=self._RECENT_CAPTIONS_MAX)
        self._latest_frame: Any = None
        self._latest_frame_seq = 0
        self._latest_preview_jpeg: bytes | None = None
        self._capture_error: Exception | None = None

        self.status = "created"
        self.started_at: datetime | None = None
        self.last_event_at: datetime | None = None
        self.last_caption: str | None = None
        self.captions_emitted = 0
        self.reconnect_count = 0
        self.lag_ms: float | None = None
        self.last_error: str | None = None

        self._backend = get_backend(InferenceConfig(model_id=self.model_id))
        self._prompt_builder = PromptBuilder()
        self._context_window = InferenceConfig().temporal_context_frames

    def start(self) -> None:
        with self._lock:
            if self._thread.is_alive():
                return
            self.status = "starting"
            self.started_at = _utcnow()
        self._thread.start()

    def stop(self) -> None:
        with self._lock:
            if self.status not in {"stopped", "stopping"}:
                self.status = "stopping"
        self._stop_event.set()
        self._thread.join(timeout=3)

    def snapshot(self) -> RTSPSessionResponse:
        with self._lock:
            return RTSPSessionResponse(
                session_id=self.session_id,
                session_name=self.session_name,
                status=self.status,
                source=self.source,
                model_id=self.model_id,
                sample_every_seconds=self.sample_every_seconds,
                started_at=self.started_at,
                last_event_at=self.last_event_at,
                last_caption=self.last_caption,
                captions_emitted=self.captions_emitted,
                reconnect_count=self.reconnect_count,
                lag_ms=self.lag_ms,
                last_error=self.last_error,
            )

    def get_preview_jpeg(self) -> bytes | None:
        with self._lock:
            return self._latest_preview_jpeg

    def _reset_live_buffers(self) -> None:
        with self._lock:
            self._latest_frame = None
            self._latest_frame_seq = 0
            self._latest_preview_jpeg = None
            self._capture_error = None

    def _get_latest_frame_snapshot(self) -> tuple[int, Any]:
        with self._lock:
            if self._latest_frame is None:
                return 0, None
            return self._latest_frame_seq, self._latest_frame.copy()

    def _set_latest_frame(self, frame: Any) -> None:
        with self._lock:
            self._latest_frame = frame
            self._latest_frame_seq += 1

    def _set_capture_error(self, error: Exception) -> None:
        with self._lock:
            self._capture_error = error

    def _get_capture_error(self) -> Exception | None:
        with self._lock:
            return self._capture_error

    async def subscribe(self) -> tuple[str, asyncio.Queue]:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue(maxsize=self._SUBSCRIBER_QUEUE_MAX)
        subscriber_id = uuid4().hex
        with self._lock:
            self._subscribers[subscriber_id] = (loop, queue)
            recent = list(self._recent_events)
        for event in recent[-self._SUBSCRIBER_QUEUE_MAX :]:
            queue.put_nowait(event)
        return subscriber_id, queue

    def unsubscribe(self, subscriber_id: str) -> None:
        with self._lock:
            self._subscribers.pop(subscriber_id, None)

    @staticmethod
    def _queue_event(queue: asyncio.Queue, event: dict[str, Any]) -> None:
        if queue.full():
            try:
                queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            pass

    def _emit(self, event: str, **data: Any) -> None:
        payload = {
            "event": event,
            "session_id": self.session_id,
            "emitted_at": _utcnow().isoformat(),
            "data": data,
        }
        with self._lock:
            self.last_event_at = _utcnow()
            self._recent_events.append(payload)
            subscribers = list(self._subscribers.values())
        for loop, queue in subscribers:
            try:
                loop.call_soon_threadsafe(self._queue_event, queue, payload)
            except RuntimeError:
                continue

    def _set_status(self, status: str, error: str | None = None) -> None:
        with self._lock:
            self.status = status
            if error is not None:
                self.last_error = error
            elif status == "running":
                self.last_error = None

    def _run(self) -> None:
        self._emit(
            "heartbeat",
            status="starting",
            captions_emitted=0,
            reconnect_count=0,
        )

        while not self._stop_event.is_set():
            self._set_status("connecting")
            self._emit("heartbeat", status="connecting")

            try:
                with LiveStreamReader(self.rtsp_url) as reader:
                    self._reset_live_buffers()
                    self._set_status("running", error=None)
                    self._emit(
                        "connected",
                        source=self.source,
                        width=reader.width,
                        height=reader.height,
                        fps=reader.fps,
                    )

                    capture_thread = threading.Thread(
                        target=self._capture_frames,
                        args=(reader,),
                        name=f"rtsp-capture-{self.session_id}",
                        daemon=True,
                    )
                    capture_thread.start()

                    last_sample_at = 0.0
                    last_heartbeat_at = 0.0
                    last_processed_frame_seq = 0

                    try:
                        while not self._stop_event.is_set():
                            now = time.monotonic()
                            capture_error = self._get_capture_error()
                            if capture_error is not None:
                                raise capture_error

                            if now - last_heartbeat_at >= self._HEARTBEAT_SECONDS:
                                snapshot = self.snapshot()
                                self._emit(
                                    "heartbeat",
                                    status=snapshot.status,
                                    captions_emitted=snapshot.captions_emitted,
                                    reconnect_count=snapshot.reconnect_count,
                                    lag_ms=snapshot.lag_ms,
                                )
                                last_heartbeat_at = now

                            if now - last_sample_at < self.sample_every_seconds:
                                time.sleep(self._IDLE_WAIT_SECONDS)
                                continue

                            frame_seq, frame = self._get_latest_frame_snapshot()
                            if frame is None or frame_seq == last_processed_frame_seq:
                                time.sleep(self._IDLE_WAIT_SECONDS)
                                continue

                            last_sample_at = now
                            last_processed_frame_seq = frame_seq
                            with self._lock:
                                seq = self.captions_emitted + 1
                                previous_captions = list(self._recent_captions)[-self._context_window :]

                            captured_at = _utcnow()
                            prompt = self._prompt_builder.build_live_frame_prompt(
                                previous_captions,
                                frame_num=seq,
                                source_label=self.session_name,
                            )

                            started = time.monotonic()
                            chunks = list(self._backend.generate_for_frame(frame, prompt))
                            caption = "".join(chunks).strip()
                            processed_at = _utcnow()
                            lag_ms = round((time.monotonic() - started) * 1000, 2)

                            with self._lock:
                                self.last_caption = caption
                                self.captions_emitted = seq
                                self.lag_ms = lag_ms
                                self._recent_captions.append(caption)

                            self._emit(
                                "caption",
                                seq=seq,
                                caption=caption,
                                captured_at=captured_at.isoformat(),
                                processed_at=processed_at.isoformat(),
                                lag_ms=lag_ms,
                            )
                    finally:
                        capture_thread.join(timeout=1.5)
            except Exception as exc:
                if self._stop_event.is_set():
                    break
                with self._lock:
                    self.reconnect_count += 1
                    self.last_error = str(exc)
                self._set_status("connecting", error=str(exc))
                self._emit(
                    "warning",
                    message=str(exc),
                    reconnect_count=self.reconnect_count,
                )
                time.sleep(self._RECONNECT_DELAY_SECONDS)

        self._set_status("stopped")
        self._emit("stopped", status="stopped")

    def _capture_frames(self, reader: LiveStreamReader) -> None:
        """Continuously pull the newest frame so preview stays responsive."""
        last_preview_at = 0.0
        try:
            while not self._stop_event.is_set():
                frame = reader.read()
                if frame is None:
                    raise IOError("Live stream frame read failed.")

                self._set_latest_frame(frame)

                now = time.monotonic()
                if now - last_preview_at >= self._PREVIEW_INTERVAL_SECONDS:
                    self._update_preview(frame)
                    last_preview_at = now
        except Exception as exc:
            self._set_capture_error(exc)

    def _update_preview(self, frame: Any) -> None:
        """Encode the latest frame as JPEG for browser preview consumption."""
        preview_frame = frame
        height, width = frame.shape[:2]
        if width > self._PREVIEW_MAX_WIDTH:
            scale = self._PREVIEW_MAX_WIDTH / float(width)
            preview_frame = cv2.resize(
                frame,
                (self._PREVIEW_MAX_WIDTH, max(1, int(height * scale))),
                interpolation=cv2.INTER_AREA,
            )
        success, buf = cv2.imencode(
            ".jpg",
            preview_frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), self._PREVIEW_JPEG_QUALITY],
        )
        if not success:
            return
        with self._lock:
            self._latest_preview_jpeg = buf.tobytes()


class RtspSessionService:
    """Registry and lifecycle manager for RTSP monitoring sessions."""

    def __init__(self, max_active_sessions: int = 2) -> None:
        self.max_active_sessions = max_active_sessions
        self._lock = threading.RLock()
        self._sessions: dict[str, RtspSession] = {}

    def create_session(self, request: RTSPSessionCreateRequest) -> RTSPSessionResponse:
        with self._lock:
            active = sum(
                1
                for session in self._sessions.values()
                if session.snapshot().status not in {"stopped"}
            )
            if active >= self.max_active_sessions:
                raise RuntimeError(
                    f"Maximum active RTSP sessions reached ({self.max_active_sessions})."
                )

            session_id = uuid4().hex
            session = RtspSession(session_id, request)
            self._sessions[session_id] = session

        session.start()
        return session.snapshot()

    def get_session(self, session_id: str) -> RTSPSession:
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"Unknown RTSP session: {session_id}")
        return session

    def list_sessions(self) -> list[RTSPSessionResponse]:
        with self._lock:
            sessions = list(self._sessions.values())
        return [session.snapshot() for session in sessions]

    def delete_session(self, session_id: str) -> RTSPSessionResponse:
        with self._lock:
            session = self._sessions.pop(session_id, None)
        if session is None:
            raise KeyError(f"Unknown RTSP session: {session_id}")
        session.stop()
        return session.snapshot()

    async def subscribe(self, session_id: str) -> tuple[RtspSession, str, asyncio.Queue]:
        session = self.get_session(session_id)
        subscriber_id, queue = await session.subscribe()
        return session, subscriber_id, queue

    def unsubscribe(self, session_id: str, subscriber_id: str) -> None:
        try:
            session = self.get_session(session_id)
        except KeyError:
            return
        session.unsubscribe(subscriber_id)

    def shutdown(self) -> None:
        with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for session in sessions:
            session.stop()


rtsp_session_service = RtspSessionService()
