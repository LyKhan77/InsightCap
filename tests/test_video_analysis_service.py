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
        self.frame_count = 810
        self.duration_seconds = 27.0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakePipeline:
    def run(self, video_path: str, time_limit_seconds=None, on_frame_done=None):
        if on_frame_done:
            on_frame_done(0, "segment-1", {"segment_index": 0, "sampled_frame_count": 10, "frame_index_start": 0, "frame_index_end": 9})
            on_frame_done(1, "segment-2", {"segment_index": 1, "sampled_frame_count": 10, "frame_index_start": 10, "frame_index_end": 19})
            on_frame_done(2, "segment-3", {"segment_index": 2, "sampled_frame_count": 7, "frame_index_start": 20, "frame_index_end": 26})
        return SimpleNamespace(
            caption="summary",
            frame_count=27,
            duration_seconds=27.0,
            device_used="cpu",
            model_id="qwen3.5:0.8b",
            video_fps=30.0,
            frame_interval=30,
        )


def parse_sse_event(chunk: str) -> tuple[str, dict]:
    lines = [line for line in chunk.strip().split("\n") if line]
    event = lines[0].split(": ", 1)[1]
    data = json.loads(lines[1].split(": ", 1)[1])
    return event, data


class VideoAnalysisServiceSegmentTest(unittest.IsolatedAsyncioTestCase):
    async def test_stream_emits_one_frame_event_per_segment(self):
        service = AnalysisService()
        params = AnalyzeParams(model="qwen3.5:0.8b")

        with patch("backend.app.services.video_analysis.VideoReader", FakeVideoReader), patch.object(
            service, "_compute_sampling", return_value=(30, 27)
        ), patch.object(service, "_build_pipeline", return_value=FakePipeline()):
            events = []
            async for chunk in service.run_stream("video.mp4", params):
                events.append(parse_sse_event(chunk))

        self.assertEqual([name for name, _ in events], ["init", "frame", "frame", "frame", "summary", "done"])
        frame_events = [data for name, data in events if name == "frame"]
        self.assertEqual([event["index"] for event in frame_events], [0, 1, 2])
        self.assertEqual([event["sampled_frame_count"] for event in frame_events], [10, 10, 7])
        self.assertEqual(frame_events[-1]["timestamp_seconds"], 20.0)
        self.assertEqual(frame_events[-1]["timestamp_end_seconds"], 26.0)
        self.assertEqual(events[-1][1]["frame_count"], 27)


if __name__ == "__main__":
    unittest.main()
