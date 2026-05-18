from __future__ import annotations

import tempfile
import time
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from backend.app.schemas.auto_label import AutoLabelConfig
from backend.app.schemas.rtsp import RTSPSessionCreateRequest
from backend.app.schemas.video import AnalyzeParams
from backend.core.config import InferenceConfig
from backend.app.services.auto_label import AutoLabelJob, Detection, YOLOEDetector, clamp_bbox, extract_caption_labels, parse_label_prompt


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


class RecordingDetector:
    def __init__(self):
        self.calls = []

    def detect(self, frame, classes, confidence):
        self.calls.append(list(classes))
        label = "forklift" if "forklift" in classes else classes[0]
        return [
            Detection(
                label=label,
                class_id=classes.index(label),
                confidence=0.82,
                bbox_xyxy=(1.0, 2.0, 5.0, 6.0),
            )
        ]


class AutoLabelServiceTest(unittest.TestCase):
    def test_default_detector_model_is_yoloe_small(self):
        self.assertEqual(AutoLabelConfig().model, "yoloe-26s-seg.pt")

    def test_captioning_defaults_use_qwen35_2b(self):
        self.assertEqual(InferenceConfig().model_id, "qwen3.5:2b")
        self.assertEqual(AnalyzeParams().model, "qwen3.5:2b")
        self.assertEqual(RTSPSessionCreateRequest(rtsp_url="rtsp://camera").model, "qwen3.5:2b")

    def test_yoloe_detector_sets_text_classes_and_exports_bboxes_only(self):
        class FakeTensor:
            def __init__(self, values):
                self._values = np.array(values)

            def __len__(self):
                return len(self._values)

            def cpu(self):
                return self

            def numpy(self):
                return self._values

        class FakeBoxes:
            xyxy = FakeTensor([[1.0, 2.0, 5.0, 6.0]])
            conf = FakeTensor([0.73])
            cls = FakeTensor([0])

        class FakeResult:
            boxes = FakeBoxes()
            names = {0: "person"}
            masks = object()

        class FakeYOLO:
            instances = []

            def __init__(self, model_name):
                self.model_name = model_name
                self.classes = []
                FakeYOLO.instances.append(self)

            def set_classes(self, classes):
                self.classes = list(classes)

            def predict(self, source, imgsz, conf, save, verbose, device):
                self.predict_args = {
                    "source": source,
                    "imgsz": imgsz,
                    "conf": conf,
                    "save": save,
                    "verbose": verbose,
                    "device": device,
                }
                return [FakeResult()]

        with patch.dict("sys.modules", {"ultralytics": types.SimpleNamespace(YOLO=FakeYOLO)}):
            detector = YOLOEDetector("yoloe-26s-seg.pt")
            detections = detector.detect(np.zeros((8, 8, 3), dtype=np.uint8), ["person"], 0.25)

        self.assertEqual(FakeYOLO.instances[0].model_name, "yoloe-26s-seg.pt")
        self.assertEqual(FakeYOLO.instances[0].classes, ["person"])
        self.assertEqual(FakeYOLO.instances[0].predict_args["device"], "0")
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0].label, "person")
        self.assertEqual(detections[0].bbox_xyxy, (1.0, 2.0, 5.0, 6.0))

    def test_prompt_parser_accepts_comma_and_newline_labels(self):
        self.assertEqual(
            parse_label_prompt("person, hard hat\nforklift"),
            ["person", "hard hat", "forklift"],
        )

    def test_caption_label_extractor_returns_object_labels_from_caption(self):
        self.assertEqual(
            extract_caption_labels("A person wearing a white shirt stands beside a forklift and a traffic cone."),
            ["person", "white shirt", "forklift", "traffic cone"],
        )

    def test_blank_prompt_uses_caption_extracted_labels_for_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            detector = RecordingDetector()
            job = AutoLabelJob(
                mode="video",
                job_id="job-1",
                config=AutoLabelConfig(
                    enabled=True,
                    prompt="",
                    duration_minutes=1,
                    confidence=0.25,
                    model="fake.pt",
                ),
                detector_factory=lambda _model: detector,
                dataset_root=Path(tmp),
            )
            job.start()
            job.enqueue_chunk(
                frames=[np.zeros((8, 8, 3), dtype=np.uint8)],
                segment_seq=1,
                caption="A person wearing a white shirt stands beside a forklift.",
                frame_seq_start=10,
                source="upload",
            )
            job.stop(drain=True)
            job.join(timeout=3)

            dataset = Path(tmp) / "video" / "job-1"
            self.assertEqual(detector.calls[0], ["person", "white shirt", "forklift"])
            self.assertIn("forklift", (dataset / "data.yaml").read_text())
            metadata = (dataset / "annotations.jsonl").read_text()
            self.assertIn('"label_prompt": ""', metadata)
            self.assertIn('"classes": ["person", "white shirt", "forklift"]', metadata)
            self.assertIn('"label": "forklift"', metadata)

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

    def test_automatic_scheduler_accepts_until_manual_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = AutoLabelJob(
                mode="rtsp",
                job_id="session-automatic",
                config=AutoLabelConfig(
                    enabled=True,
                    prompt="person",
                    schedule_mode="automatic",
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
                caption="person after duration window",
                frame_seq_start=1,
                source="camera",
            )
            snapshot = job.snapshot()
            job.stop(drain=True)
            job.join(timeout=3)

            self.assertTrue(accepted)
            self.assertEqual(snapshot.status, "active")
            self.assertIsNone(snapshot.remaining_seconds)
            self.assertEqual(job.snapshot().frames_labelled, 1)


if __name__ == "__main__":
    unittest.main()
