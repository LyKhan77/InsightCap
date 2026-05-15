from __future__ import annotations

import asyncio
import dataclasses
import json
from uuid import uuid4
from typing import AsyncIterator, Optional

from backend.core.config import InferenceConfig, SamplerConfig
from backend.core.pipeline import CaptionPipeline
from backend.core.video.reader import VideoReader

from backend.app.services.auto_label import AutoLabelJob

from backend.app.schemas.video import AnalysisResponse, AnalyzeParams


class AnalysisService:
    """Async bridge between FastAPI routes and the synchronous CaptionPipeline."""

    _MAX_FRAMES = 60  # hard cap — keeps inference time manageable

    def _compute_sampling(self, video_fps: float, total_native: int) -> tuple[int, int]:
        """Return (frame_interval, max_frames) auto-computed from video metadata.

        Strategy: ~1 frame per second of video, capped at _MAX_FRAMES.
        """
        frame_interval = max(1, round(video_fps))  # 1 capture per second
        indices = list(range(0, total_native, frame_interval))[: self._MAX_FRAMES]
        return frame_interval, len(indices)

    def _build_pipeline(
        self,
        model: str,
        frame_interval: int,
        frame_prompt: Optional[str] = None,
        summary_prompt: Optional[str] = None,
    ) -> CaptionPipeline:
        inference_config = InferenceConfig(model_id=model, backend="vllm")
        if frame_prompt:
            inference_config.frame_prompt = frame_prompt
        if summary_prompt:
            inference_config.summary_prompt = summary_prompt

        return CaptionPipeline(
            sampler_config=SamplerConfig(frame_interval=frame_interval, max_frames=self._MAX_FRAMES),
            inference_config=inference_config,
        )

    async def run(self, video_path: str, params: AnalyzeParams) -> AnalysisResponse:
        """Run the full pipeline and return a complete AnalysisResponse."""
        try:
            with VideoReader(video_path) as _vr:
                video_fps = _vr.fps
                total_native = int(_vr.frame_count)
        except Exception:
            video_fps = 30.0
            total_native = 0
        frame_interval, _ = self._compute_sampling(video_fps, total_native)
        pipeline = self._build_pipeline(
            params.model,
            frame_interval,
            frame_prompt=params.frame_prompt,
            summary_prompt=params.summary_prompt,
        )
        auto_label_job = None
        if params.auto_label.enabled:
            auto_label_job = AutoLabelJob(
                mode="video",
                job_id=uuid4().hex,
                config=params.auto_label,
            )
            auto_label_job.start()

        def on_segment_done(segment_index: int, caption: str, frames: list, metadata: dict) -> None:
            if auto_label_job is None:
                return
            frame_start = int(metadata.get("frame_index_start", segment_index))
            auto_label_job.enqueue_chunk(
                frames=frames,
                segment_seq=segment_index + 1,
                caption=caption,
                frame_seq_start=frame_start,
                source=video_path,
            )

        def _run_pipeline():
            result = pipeline.run(video_path, on_segment_done=on_segment_done)
            if auto_label_job is not None:
                auto_label_job.stop(drain=True)
                auto_label_job.join()
            return result

        result = await asyncio.to_thread(_run_pipeline)
        return AnalysisResponse(**dataclasses.asdict(result))

    async def run_stream(
        self, video_path: str, params: AnalyzeParams
    ) -> AsyncIterator[str]:
        """Run the pipeline and yield Server-Sent Events as each frame completes.

        Event types:
          - init:    {"total_frames": N, "video_fps": F, "duration_seconds": D}
          - frame:   {"index": N, "caption": "...", "timestamp_seconds": T}
          - summary: {"caption": "..."}
          - done:    {"frame_count": N, "duration_seconds": F, "device_used": "...", "model_id": "..."}
        """
        def _sse(event: str, data: dict) -> str:
            return f"event: {event}\ndata: {json.dumps(data)}\n\n"

        # Read video metadata to compute sampling params and emit init event.
        try:
            with VideoReader(video_path) as _vr:
                video_fps = _vr.fps
                total_native = int(_vr.frame_count)
                duration = _vr.duration_seconds
        except Exception:
            video_fps = 30.0
            total_native = 0
            duration = 0.0

        frame_interval, total_frames = self._compute_sampling(video_fps, total_native)

        # Emit init event BEFORE starting pipeline — frontend uses this to
        # show correct total and trigger video autoplay.
        yield _sse("init", {
            "total_frames": total_frames,
            "video_fps": video_fps,
            "duration_seconds": duration,
        })

        loop = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def on_frame_done(idx: int, caption: str, metadata: dict | None = None) -> None:
            metadata = metadata or {}
            frame_start = int(metadata.get("frame_index_start", idx))
            frame_end = int(metadata.get("frame_index_end", frame_start))
            timestamp = (frame_start * frame_interval) / video_fps if video_fps > 0 else 0.0
            timestamp_end = (frame_end * frame_interval) / video_fps if video_fps > 0 else timestamp
            payload = {
                "index": int(metadata.get("segment_index", idx)),
                "caption": caption,
                "timestamp_seconds": timestamp,
                "timestamp_end_seconds": timestamp_end,
                "sampled_frame_count": metadata.get("sampled_frame_count"),
                "frame_index_start": frame_start,
                "frame_index_end": frame_end,
            }
            loop.call_soon_threadsafe(queue.put_nowait, payload)

        result_holder: list = []
        auto_label_job = None
        if params.auto_label.enabled:
            auto_label_job = AutoLabelJob(
                mode="video",
                job_id=uuid4().hex,
                config=params.auto_label,
            )
            auto_label_job.start()
            yield _sse("auto_label_started", auto_label_job.snapshot().model_dump(mode="json"))

        def on_segment_done(segment_index: int, caption: str, frames: list, metadata: dict) -> None:
            if auto_label_job is None:
                return
            frame_start = int(metadata.get("frame_index_start", segment_index))
            auto_label_job.enqueue_chunk(
                frames=frames,
                segment_seq=segment_index + 1,
                caption=caption,
                frame_seq_start=frame_start,
                source=video_path,
            )
            loop.call_soon_threadsafe(
                queue.put_nowait,
                {"__event__": "auto_label_frame", **auto_label_job.snapshot().model_dump(mode="json")},
            )

        def _run_pipeline() -> None:
            pipeline = self._build_pipeline(
                params.model,
                frame_interval,
                frame_prompt=params.frame_prompt,
                summary_prompt=params.summary_prompt,
            )
            result = pipeline.run(
                video_path,
                time_limit_seconds=duration,
                on_frame_done=on_frame_done,
                on_segment_done=on_segment_done,
            )
            if auto_label_job is not None:
                auto_label_job.stop(drain=True)
                auto_label_job.join()
            result_holder.append(result)
            loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel

        asyncio.ensure_future(asyncio.to_thread(_run_pipeline))

        while True:
            item = await queue.get()
            if item is None:
                break
            if isinstance(item, dict) and item.get("__event__"):
                event_name = item.pop("__event__")
                yield _sse(event_name, item)
                continue
            yield _sse("frame", item)

        if result_holder:
            result = result_holder[0]
            yield _sse("summary", {"caption": result.caption})
            yield _sse("done", {
                "frame_count": result.frame_count,
                "duration_seconds": result.duration_seconds,
                "device_used": result.device_used,
                "model_id": result.model_id,
                "video_fps": result.video_fps,
                "frame_interval": result.frame_interval,
                "auto_label": auto_label_job.snapshot().model_dump(mode="json") if auto_label_job is not None else None,
            })
            if auto_label_job is not None:
                yield _sse("auto_label_done", auto_label_job.snapshot().model_dump(mode="json"))
