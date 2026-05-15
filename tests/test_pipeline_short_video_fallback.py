from __future__ import annotations

import unittest
from unittest.mock import patch

import numpy as np

from backend.core.config import InferenceConfig, SamplerConfig
from backend.core.pipeline import CaptionPipeline


class FakeVideoReader:
    def __init__(self, path: str) -> None:
        self.path = path
        self.duration_seconds = 9.5
        self.fps = 30.0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeBackend:
    def __init__(self) -> None:
        self.frame_calls: list[str] = []
        self.frames_calls: list[tuple[int, str]] = []
        self.summarize_calls: list[list[str]] = []

    def generate_for_frame(self, frame, prompt):
        self.frame_calls.append(prompt)
        yield f"frame-{len(self.frame_calls)}"

    def generate_for_frames(self, frames, prompt):
        self.frames_calls.append((len(frames), prompt))
        yield "short-video-caption"

    def summarize(self, frame_captions, summary_prompt):
        self.summarize_calls.append(list(frame_captions))
        yield "final-summary"


class ShortVideoFallbackPipelineTest(unittest.TestCase):
    def _build_pipeline(self, backend: FakeBackend, frames):
        with patch("backend.core.pipeline.get_backend", return_value=backend):
            pipeline = CaptionPipeline(
                sampler_config=SamplerConfig(frame_interval=30, max_frames=20),
                inference_config=InferenceConfig(model_id="qwen3.5:0.8b", backend="vllm"),
            )
        pipeline._sampler = type("Sampler", (), {"sample": lambda self, reader: frames})()
        return pipeline

    def test_short_video_uses_single_segment_caption(self):
        backend = FakeBackend()
        frames = [np.zeros((4, 4, 3), dtype=np.uint8) for _ in range(3)]
        pipeline = self._build_pipeline(backend, frames)
        done_calls = []

        with patch("backend.core.pipeline.VideoReader", FakeVideoReader):
            result = pipeline.run("video.mp4", on_frame_done=lambda idx, caption: done_calls.append((idx, caption)))

        self.assertEqual(result.frame_count, 3)
        self.assertEqual(result.frame_captions, ["short-video-caption"])
        self.assertEqual(result.caption, "final-summary")
        self.assertEqual(done_calls, [(0, "short-video-caption")])
        self.assertEqual(len(backend.frames_calls), 1)
        self.assertEqual(backend.frames_calls[0][0], 3)
        self.assertEqual(backend.frame_calls, [])
        self.assertEqual(backend.summarize_calls, [["short-video-caption"]])

    def test_ten_or_more_frames_uses_segment_path(self):
        backend = FakeBackend()
        frames = [np.zeros((4, 4, 3), dtype=np.uint8) for _ in range(10)]
        pipeline = self._build_pipeline(backend, frames)

        with patch("backend.core.pipeline.VideoReader", FakeVideoReader):
            result = pipeline.run("video.mp4")

        self.assertEqual(result.frame_count, 10)
        self.assertEqual(result.frame_captions, ["short-video-caption"])
        self.assertEqual(backend.frame_calls, [])
        self.assertEqual(len(backend.frames_calls), 1)
        self.assertEqual(backend.frames_calls[0][0], 10)

    def test_zero_frames_keeps_existing_no_frames_behavior(self):
        backend = FakeBackend()
        pipeline = self._build_pipeline(backend, [])

        with patch("backend.core.pipeline.VideoReader", FakeVideoReader):
            result = pipeline.run("video.mp4")

        self.assertEqual(result.frame_count, 0)
        self.assertEqual(result.frame_captions, [])
        self.assertEqual(result.caption, "No frames could be extracted from the video.")
        self.assertEqual(backend.frame_calls, [])
        self.assertEqual(backend.frames_calls, [])
        self.assertEqual(backend.summarize_calls, [])


if __name__ == "__main__":
    unittest.main()
