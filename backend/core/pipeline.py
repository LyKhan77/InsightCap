from __future__ import annotations

import time
from dataclasses import dataclass

from backend.core.config import InferenceConfig, SamplerConfig
from backend.core.device import detect_device
from backend.core.inference.factory import get_backend
from backend.core.prompt.builder import PromptBuilder
from backend.core.video.reader import VideoReader
from backend.core.video.sampler import FrameSampler


@dataclass
class CaptionResult:
    caption: str
    frame_captions: list[str]
    frame_count: int
    duration_seconds: float
    device_used: str
    model_id: str
    video_fps: float
    frame_interval: int


class CaptionPipeline:
    """Orchestrates video reading, frame sampling, and caption generation."""

    def __init__(
        self,
        sampler_config: SamplerConfig | None = None,
        inference_config: InferenceConfig | None = None,
    ) -> None:
        self.sampler_config = sampler_config or SamplerConfig()
        self.inference_config = inference_config or InferenceConfig()
        self._sampler = FrameSampler(self.sampler_config)
        self._backend = get_backend(self.inference_config)
        self._prompt_builder = PromptBuilder(
            frame_prompt=self.inference_config.frame_prompt
        )

    def run(
        self,
        video_path: str,
        time_limit_seconds: float | None = None,
        on_frame_start: callable | None = None,
        on_frame_token: callable | None = None,
        on_frame_done: callable | None = None,
        on_summary_token: callable | None = None,
    ) -> CaptionResult:
        """Run the full captioning pipeline on a local video file.

        Args:
            video_path: Path to the local video file.
            on_frame_start: Optional callback(frame_index, total_frames).
            on_frame_token: Optional callback(token: str).
            on_frame_done: Optional callback(frame_index, caption: str).
            on_summary_token: Optional callback(token: str) for summary streaming.
        """
        with VideoReader(video_path) as reader:
            duration = reader.duration_seconds
            video_fps = reader.fps
            frames = self._sampler.sample(reader)

        if not frames:
            return CaptionResult(
                caption="No frames could be extracted from the video.",
                frame_captions=[],
                frame_count=0,
                duration_seconds=duration,
                device_used=detect_device(),
                model_id=self.inference_config.model_id,
                video_fps=video_fps,
                frame_interval=self.sampler_config.frame_interval,
            )

        frame_captions: list[str] = []
        total = len(frames)
        n_context = self.inference_config.temporal_context_frames
        deadline = time.monotonic() + time_limit_seconds if time_limit_seconds else None

        for i, frame in enumerate(frames):
            if deadline and time.monotonic() > deadline:
                break  # video has ended — stop processing remaining frames
            if on_frame_start:
                on_frame_start(i, total)

            # Build context-aware prompt using last N completed captions
            previous = frame_captions[-n_context:] if n_context > 0 else []
            message = self._prompt_builder.build_frame_message_with_context(
                frame,
                previous_captions=previous,
                frame_num=i + 1,
                total_frames=total,
            )
            context_prompt = message["content"]

            tokens: list[str] = []
            for token in self._backend.generate_for_frame(frame, context_prompt):
                tokens.append(token)
                if on_frame_token:
                    on_frame_token(token)

            caption = "".join(tokens).strip()
            frame_captions.append(caption)

            if on_frame_done:
                on_frame_done(i, caption)

        # Generate overall narrative summary
        summary_tokens: list[str] = []
        for token in self._backend.summarize(
            frame_captions, self.inference_config.summary_prompt
        ):
            summary_tokens.append(token)
            if on_summary_token:
                on_summary_token(token)

        summary = "".join(summary_tokens).strip()

        return CaptionResult(
            caption=summary,
            frame_captions=frame_captions,
            frame_count=total,
            duration_seconds=duration,
            device_used=detect_device(),
            model_id=self.inference_config.model_id,
            video_fps=video_fps,
            frame_interval=self.sampler_config.frame_interval,
        )
