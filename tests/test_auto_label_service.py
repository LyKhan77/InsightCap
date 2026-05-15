from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

import numpy as np

from backend.app.schemas.auto_label import AutoLabelConfig
from backend.app.services.auto_label import AutoLabelJob, Detection, clamp_bbox, parse_label_prompt


class FakeDetector:
    def detect(self, frame, classes, confidence):
        return [
            Detection(
                label=classes[0],
                class_id=0,
                confidence=0.8,
                bbox_xyxy=(1.0, 2.0, 5.0, 6.0),
            )
        ]


class AutoLabelServiceTest(unittest.TestCase):
    def test_prompt_parser_accepts_comma_and_newline_labels(self):
        self.assertEqual(
            parse_label_prompt("person, hard hat\nforklift"),
            ["person", "hard hat", "forklift"],
        )

    def test_bbox_clamp_keeps_coordinates_inside_image(self):
        self.assertEqual(clamp_bbox((-2, 1, 20, 30), 10, 12), (0.0, 1, 10.0, 12.0))

    def test_job_exports_yolo_jsonl_overlay_and_data_yaml(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = AutoLabelJob(
                mode="rtsp",
                job_id="session-1",
                config=AutoLabelConfig(
                    enabled=True,
                    prompt="person",
                    duration_minutes=1,
                    confidence=0.25,
                    model="fake.pt",
                ),
                detector_factory=lambda _model: FakeDetector(),
                dataset_root=Path(tmp),
            )
            job.start()
            job.enqueue_chunk(
                frames=[np.zeros((8, 8, 3), dtype=np.uint8)],
                segment_seq=1,
                caption="person near gate",
                frame_seq_start=10,
                source="rtsp://camera",
            )
            job.stop(drain=True)
            job.join(timeout=3)

            dataset = Path(tmp) / "rtsp" / "session-1"
            self.assertTrue((dataset / "images" / "segment_000001_frame_000010.jpg").exists())
            self.assertTrue((dataset / "overlays" / "segment_000001_frame_000010.jpg").exists())
            self.assertEqual(
                (dataset / "labels" / "segment_000001_frame_000010.txt").read_text().strip(),
                "0 0.375000 0.500000 0.500000 0.500000",
            )
            self.assertIn("person", (dataset / "data.yaml").read_text())
            self.assertIn("person near gate", (dataset / "annotations.jsonl").read_text())
            self.assertEqual(job.snapshot().frames_labelled, 1)

    def test_expired_scheduler_rejects_new_chunks_without_stopping_owner(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = AutoLabelJob(
                mode="rtsp",
                job_id="session-2",
                config=AutoLabelConfig(
                    enabled=True,
                    prompt="person",
                    duration_minutes=0.001,
                    confidence=0.25,
                    model="fake.pt",
                ),
                detector_factory=lambda _model: FakeDetector(),
                dataset_root=Path(tmp),
            )
            job.start()
            time.sleep(0.08)
            accepted = job.enqueue_chunk(
                frames=[np.zeros((8, 8, 3), dtype=np.uint8)],
                segment_seq=1,
                caption="late",
                frame_seq_start=1,
                source="camera",
            )
            job.join(timeout=3)

            self.assertFalse(accepted)
            self.assertEqual(job.snapshot().status, "done")


if __name__ == "__main__":
    unittest.main()
