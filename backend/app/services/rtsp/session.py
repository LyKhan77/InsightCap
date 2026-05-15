from __future__ import annotations

import asyncio
import threading
import time
from collections import deque
from datetime import datetime
from typing import Any
from uuid import uuid4

import cv2

from backend.core.config import InferenceConfig
from backend.core.inference.factory import get_backend
from backend.core.prompt.builder import PromptBuilder
from backend.core.video.live_reader import LiveStreamReader

from backend.app.schemas.rtsp import RTSPSessionCreateRequest, RTSPSessionResponse
from backend.app.services.rtsp.utils import (
    default_session_name,
    mask_error_message,
    mask_rtsp_url,
    utcnow,
)


class RtspSession:
    """Owns one RTSP monitoring session and its worker thread."""

    _HEARTBEAT_SECONDS = 5.0
    _RECONNECT_DELAY_SECONDS = 2.0
    _IDLE_WAIT_SECONDS = 0.05
    _RECENT_EVENTS_MAX = 32
    _RECENT_CAPTIONS_MAX = 8
    _SUBSCRIBER_QUEUE_MAX = 32
    _PREVIEW_INTERVAL_SECONDS = 0.1
    _PREVIEW_MAX_WIDTH = 960
    _PREVIEW_JPEG_QUALITY = 70
    _MAX_CONSECUTIVE_READ_FAILURES = 240
    _SEGMENT_FRAME_COUNT = 10
    _SEGMENT_CONTEXT_CAPTIONS = 1

    def __init__(self, session_id: str, request: RTSPSessionCreateRequest) -> None:
        self.session_id = session_id
        self.rtsp_url = request.rtsp_url
        self.source = mask_rtsp_url(request.rtsp_url)
        self.session_name = request.session_name or default_session_name(request.rtsp_url)
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
        self._segment_frames: list[tuple[int, Any]] = []

        self.status = "created"
        self.started_at: datetime | None = None
        self.last_event_at: datetime | None = None
        self.last_caption: str | None = None
        self.captions_emitted = 0
        self.reconnect_count = 0
        self.lag_ms: float | None = None
        self.last_error: str | None = None

        inference_config = InferenceConfig(model_id=self.model_id, backend="vllm")
        if request.frame_prompt:
            inference_config.frame_prompt = request.frame_prompt

        self._backend = get_backend(inference_config)
        self._prompt_builder = PromptBuilder(frame_prompt=inference_config.frame_prompt)

    def start(self) -> None:
        with self._lock:
            if self._thread.is_alive():
                return
            self.status = "starting"
            self.started_at = utcnow()
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
            self._segment_frames.clear()

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
            "emitted_at": utcnow().isoformat(),
            "data": data,
        }
        with self._lock:
            self.last_event_at = utcnow()
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
                            self._process_sampled_live_frame(frame_seq, frame)
                    finally:
                        capture_thread.join(timeout=1.5)
            except Exception as exc:
                if self._stop_event.is_set():
                    break
                error_message = mask_error_message(str(exc), self.rtsp_url, self.source)
                with self._lock:
                    self.reconnect_count += 1
                    self.last_error = error_message
                self._set_status("connecting", error=error_message)
                self._emit(
                    "warning",
                    message=error_message,
                    reconnect_count=self.reconnect_count,
                )
                time.sleep(self._RECONNECT_DELAY_SECONDS)

        self._set_status("stopped")
        self._emit("stopped", status="stopped")

    def _process_sampled_live_frame(self, frame_seq: int, frame: Any) -> None:
        """Add one sampled frame and emit a caption when a full segment is ready."""
        with self._lock:
            self._segment_frames.append((frame_seq, frame.copy()))
            if len(self._segment_frames) < self._SEGMENT_FRAME_COUNT:
                return

            segment = self._segment_frames[: self._SEGMENT_FRAME_COUNT]
            self._segment_frames = self._segment_frames[self._SEGMENT_FRAME_COUNT :]
            seq = self.captions_emitted + 1
            previous_captions = list(self._recent_captions)[-self._SEGMENT_CONTEXT_CAPTIONS :]

        frame_seq_start = segment[0][0]
        frame_seq_end = segment[-1][0]
        frames = [item[1] for item in segment]
        captured_at = utcnow()
        prompt = self._prompt_builder.build_live_segment_prompt(
            previous_captions,
            segment_num=seq,
            source_label=self.session_name,
            sampled_frame_count=len(frames),
        )

        started = time.monotonic()
        chunks = list(self._backend.generate_for_frames(frames, prompt))
        caption = "".join(chunks).strip()
        processed_at = utcnow()
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
            sampled_frame_count=len(frames),
            frame_seq_start=frame_seq_start,
            frame_seq_end=frame_seq_end,
            captured_at=captured_at.isoformat(),
            processed_at=processed_at.isoformat(),
            lag_ms=lag_ms,
        )

    def _capture_frames(self, reader: LiveStreamReader) -> None:
        """Continuously pull the newest frame so preview stays responsive."""
        last_preview_at = 0.0
        consecutive_failures = 0
        try:
            while not self._stop_event.is_set():
                frame = reader.read()
                if frame is None:
                    consecutive_failures += 1
                    if consecutive_failures >= self._MAX_CONSECUTIVE_READ_FAILURES:
                        raise IOError(
                            "Live stream frame read failed after "
                            f"{round(consecutive_failures * self._IDLE_WAIT_SECONDS, 1)} seconds."
                        )
                    time.sleep(self._IDLE_WAIT_SECONDS)
                    continue

                consecutive_failures = 0
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
