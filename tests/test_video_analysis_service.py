from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.app.schemas.video import AnalyzeParams
from backend.app.services.video_analysis import AnalysisService


class FakeVideoReader:
    def __init__(self, path: str) -> None:
        self.path = path
        self.fps = 30.0
        self.frame_count = 300
        self.duration_seconds = 9.0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakePipeline:
    def __init__(self, frame_events: list[tuple[int, str]], result):
        self._frame_events = frame_events
        self._result = result

    def run(self, video_path: str, time_limit_seconds=None, on_frame_done=None):
        if on_frame_done:
            for idx, caption in self._frame_events:
                on_frame_done(idx, caption)
        return self._result


def parse_sse_event(chunk: str) -> tuple[str, dict]:
    lines = [line for line in chunk.strip().split("\n") if line]
    event = lines[0].split(": ", 1)[1]
    data = json.loads(lines[1].split(": ", 1)[1])
    return event, data


class VideoAnalysisServiceStreamTest(unittest.IsolatedAsyncioTestCase):
    async def test_stream_short_video_emits_single_frame_event(self):
        service = AnalysisService()
        params = AnalyzeParams(model="qwen3.5:0.8b")
        result = SimpleNamespace(
            caption="summary-short",
            frame_count=3,
            duration_seconds=9.0,
            device_used="cpu",
            model_id="qwen3.5:0.8b",
            video_fps=30.0,
            frame_interval=30,
        )
        pipeline = FakePipeline([(0, "short-caption")], result)

        with patch("backend.app.services.video_analysis.VideoReader", FakeVideoReader), patch.object(
            service, "_compute_sampling", return_value=(30, 3)
        ), patch.object(service, "_build_pipeline", return_value=pipeline):
            events = []
            async for chunk in service.run_stream("video.mp4", params):
                events.append(parse_sse_event(chunk))

        self.assertEqual([name for name, _ in events], ["init", "frame", "summary", "done"])
        self.assertEqual(events[1][1]["index"], 0)
        self.assertEqual(events[1][1]["caption"], "short-caption")
        self.assertEqual(events[3][1]["frame_count"], 3)

    async def test_stream_normal_video_keeps_multi_frame_events(self):
        service = AnalysisService()
        params = AnalyzeParams(model="qwen3.5:0.8b")
        result = SimpleNamespace(
            caption="summary-normal",
            frame_count=12,
            duration_seconds=12.0,
            device_used="cpu",
            model_id="qwen3.5:0.8b",
            video_fps=30.0,
            frame_interval=30,
        )
        pipeline = FakePipeline(
            [(0, "frame-1"), (1, "frame-2"), (2, "frame-3")],
            result,
        )

        with patch("backend.app.services.video_analysis.VideoReader", FakeVideoReader), patch.object(
            service, "_compute_sampling", return_value=(30, 12)
        ), patch.object(service, "_build_pipeline", return_value=pipeline):
            events = []
            async for chunk in service.run_stream("video.mp4", params):
                events.append(parse_sse_event(chunk))

        names = [name for name, _ in events]
        self.assertEqual(names[0], "init")
        self.assertEqual(names[-2:], ["summary", "done"])
        frame_events = [event for event in events if event[0] == "frame"]
        self.assertEqual(len(frame_events), 3)
        self.assertEqual(events[-1][1]["frame_count"], 12)

    async def test_stream_zero_frames_keeps_existing_no_frame_events(self):
        service = AnalysisService()
        params = AnalyzeParams(model="qwen3.5:0.8b")
        result = SimpleNamespace(
            caption="No frames could be extracted from the video.",
            frame_count=0,
            duration_seconds=0.0,
            device_used="cpu",
            model_id="qwen3.5:0.8b",
            video_fps=30.0,
            frame_interval=30,
        )
        pipeline = FakePipeline([], result)

        with patch("backend.app.services.video_analysis.VideoReader", FakeVideoReader), patch.object(
            service, "_compute_sampling", return_value=(30, 0)
        ), patch.object(service, "_build_pipeline", return_value=pipeline):
            events = []
            async for chunk in service.run_stream("video.mp4", params):
                events.append(parse_sse_event(chunk))

        self.assertEqual([name for name, _ in events], ["init", "summary", "done"])
        self.assertEqual(events[-1][1]["frame_count"], 0)


if __name__ == "__main__":
    unittest.main()
