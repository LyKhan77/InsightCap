from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import patch

sys.modules.setdefault("cv2", types.SimpleNamespace())
sys.modules.setdefault("PIL", types.SimpleNamespace(Image=types.SimpleNamespace()))
sys.modules.setdefault("torch", types.SimpleNamespace())

from backend.core.config import InferenceConfig, SamplerConfig
from backend.core.pipeline import CaptionPipeline


class FakeVideoReader:
    def __init__(self, path: str) -> None:
        self.path = path
        self.duration_seconds = 27.0
        self.fps = 30.0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeBackend:
    def __init__(self) -> None:
        self.frame_calls = []
        self.segment_calls = []

    def generate_for_frame(self, frame, prompt):
        self.frame_calls.append((frame, prompt))
        yield "unused"

    def generate_for_frames(self, frames, prompt):
        self.segment_calls.append((len(frames), prompt))
        yield f"segment-{len(self.segment_calls)}"

    def summarize(self, frame_captions, summary_prompt):
        yield "summary"


class VideoSegmentPipelineTest(unittest.TestCase):
    def test_twenty_seven_sampled_frames_emit_ten_ten_seven_segments(self):
        backend = FakeBackend()
        frames = [object() for _ in range(27)]
        done_calls = []

        with patch("backend.core.pipeline.get_backend", return_value=backend):
            pipeline = CaptionPipeline(
                sampler_config=SamplerConfig(frame_interval=30, max_frames=60),
                inference_config=InferenceConfig(model_id="qwen3.5:0.8b", backend="vllm"),
            )
        pipeline._sampler = type("Sampler", (), {"sample": lambda self, reader: frames})()

        with patch("backend.core.pipeline.VideoReader", FakeVideoReader), patch(
            "backend.core.pipeline.detect_device", return_value="cpu"
        ):
            result = pipeline.run(
                "video.mp4",
                on_frame_done=lambda idx, caption, metadata: done_calls.append((idx, caption, metadata)),
            )

        self.assertEqual(result.frame_count, 27)
        self.assertEqual(result.frame_captions, ["segment-1", "segment-2", "segment-3"])
        self.assertEqual([call[0] for call in backend.segment_calls], [10, 10, 7])
        self.assertEqual(backend.frame_calls, [])
        self.assertEqual([call[0] for call in done_calls], [0, 1, 2])
        self.assertEqual([call[2]["sampled_frame_count"] for call in done_calls], [10, 10, 7])
        self.assertEqual(done_calls[-1][2]["frame_index_start"], 20)
        self.assertEqual(done_calls[-1][2]["frame_index_end"], 26)


if __name__ == "__main__":
    unittest.main()
