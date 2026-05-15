from __future__ import annotations

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

    _SEGMENT_FRAME_COUNT = 10

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
        total_segments = (total + self._SEGMENT_FRAME_COUNT - 1) // self._SEGMENT_FRAME_COUNT
        n_context = self.inference_config.temporal_context_frames

        for segment_index, chunk_start in enumerate(range(0, total, self._SEGMENT_FRAME_COUNT)):
            segment = frames[chunk_start : chunk_start + self._SEGMENT_FRAME_COUNT]
            if on_frame_start:
                on_frame_start(segment_index, total_segments)

            previous = frame_captions[-n_context:] if n_context > 0 else []
            prompt = self._prompt_builder.build_video_segment_prompt(
                previous_captions=previous,
                segment_num=segment_index + 1,
                sampled_frame_count=len(segment),
            )

            tokens: list[str] = []
            for token in self._backend.generate_for_frames(segment, prompt):
                tokens.append(token)
                if on_frame_token:
                    on_frame_token(token)

            caption = "".join(tokens).strip()
            frame_captions.append(caption)

            if on_frame_done:
                metadata = {
                    "segment_index": segment_index,
                    "sampled_frame_count": len(segment),
                    "frame_index_start": chunk_start,
                    "frame_index_end": chunk_start + len(segment) - 1,
                }
                on_frame_done(segment_index, caption, metadata)

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
