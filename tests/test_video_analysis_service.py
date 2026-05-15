from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.app.schemas.auto_label import AutoLabelConfig, AutoLabelStatus
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
    def run(self, video_path: str, time_limit_seconds=None, on_frame_done=None, on_segment_done=None):
        segments = [
            (0, "segment-1", {"segment_index": 0, "sampled_frame_count": 10, "frame_index_start": 0, "frame_index_end": 9}),
            (1, "segment-2", {"segment_index": 1, "sampled_frame_count": 10, "frame_index_start": 10, "frame_index_end": 19}),
            (2, "segment-3", {"segment_index": 2, "sampled_frame_count": 7, "frame_index_start": 20, "frame_index_end": 26}),
        ]
        for idx, caption, metadata in segments:
            if on_frame_done:
                on_frame_done(idx, caption, metadata)
            if on_segment_done:
                on_segment_done(idx, caption, [object()] * metadata["sampled_frame_count"], metadata)
        return SimpleNamespace(
            caption="summary",
            frame_count=27,
            duration_seconds=27.0,
            device_used="cpu",
            model_id="qwen3.5:0.8b",
            video_fps=30.0,
            frame_interval=30,
        )




class FakeAutoLabelJob:
    instances = []

    def __init__(self, mode, job_id, config):
        self.mode = mode
        self.job_id = job_id
        self.config = config
        self.enqueued = []
        self.status = "idle"
        FakeAutoLabelJob.instances.append(self)

    def start(self):
        self.status = "active"

    def stop(self, drain=True):
        self.status = "done"

    def join(self, timeout=None):
        return None

    def snapshot(self):
        return AutoLabelStatus(
            status=self.status,
            frames_labelled=len(self.enqueued),
            frames_dropped=0,
            chunks_enqueued=len(self.enqueued),
        )

    def enqueue_chunk(self, frames, segment_seq, caption, frame_seq_start, source):
        self.enqueued.append((list(frames), segment_seq, caption, frame_seq_start, source))
        return True


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

    async def test_stream_auto_labelling_follows_video_segments(self):
        service = AnalysisService()
        params = AnalyzeParams(
            model="qwen3.5:0.8b",
            auto_label=AutoLabelConfig(
                enabled=True,
                prompt="person",
                duration_minutes=1,
                confidence=0.25,
            ),
        )
        FakeAutoLabelJob.instances = []

        with patch("backend.app.services.video_analysis.VideoReader", FakeVideoReader), patch.object(
            service, "_compute_sampling", return_value=(30, 27)
        ), patch.object(service, "_build_pipeline", return_value=FakePipeline()), patch(
            "backend.app.services.video_analysis.AutoLabelJob", FakeAutoLabelJob
        ):
            events = []
            async for chunk in service.run_stream("video.mp4", params):
                events.append(parse_sse_event(chunk))

        event_names = [name for name, _ in events]
        self.assertIn("auto_label_started", event_names)
        self.assertIn("auto_label_done", event_names)
        self.assertEqual(len(FakeAutoLabelJob.instances), 1)
        job = FakeAutoLabelJob.instances[0]
        self.assertEqual(len(job.enqueued), 3)
        self.assertEqual([len(item[0]) for item in job.enqueued], [10, 10, 7])
        self.assertEqual(events[-2][1]["auto_label"]["status"], "done")


if __name__ == "__main__":
    unittest.main()
