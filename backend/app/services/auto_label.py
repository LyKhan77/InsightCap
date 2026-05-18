from __future__ import annotations

import json
import os
import queue
import re
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterable, Optional

import cv2
import numpy as np

from backend.app.schemas.auto_label import AutoLabelConfig, AutoLabelStatus


DATASET_ROOT = Path("datasets/auto-label")
DEFAULT_QUEUE_SIZE = 96
DEFAULT_IMAGE_SIZE = 640


@dataclass(frozen=True)
class Detection:
    label: str
    class_id: int
    confidence: float
    bbox_xyxy: tuple[float, float, float, float]


@dataclass(frozen=True)
class AutoLabelFrame:
    frame: np.ndarray
    segment_seq: int
    frame_seq: int
    frame_offset: int
    caption: str
    source: str
    captured_at: datetime


class YOLOEDetector:
    """Thin lazy wrapper around Ultralytics YOLOE for bbox-only object export."""

    def __init__(self, model_name: str, image_size: int = DEFAULT_IMAGE_SIZE, device: str | None = None) -> None:
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                "Auto-Labelling requires ultralytics. Install it with: pip install ultralytics"
            ) from exc

        self.model_name = model_name
        self.image_size = image_size
        self.device = device if device is not None else os.getenv("AUTO_LABEL_GPU_DEVICE", "0")
        self._model = YOLO(model_name)
        self._classes: list[str] = []

    def detect(self, frame: np.ndarray, classes: list[str], confidence: float) -> list[Detection]:
        if classes != self._classes:
            self._model.set_classes(classes)
            self._classes = list(classes)

        results = self._model.predict(
            source=frame,
            imgsz=self.image_size,
            conf=confidence,
            save=False,
            verbose=False,
            device=self.device,
        )
        if not results:
            return []

        result = results[0]
        boxes = getattr(result, "boxes", None)
        if boxes is None or len(boxes.xyxy) == 0:
            return []

        xyxy = boxes.xyxy.cpu().numpy()
        conf = boxes.conf.cpu().numpy()
        cls = boxes.cls.cpu().numpy().astype(int)
        names = getattr(result, "names", {}) or {}

        detections: list[Detection] = []
        for idx, coords in enumerate(xyxy):
            class_id = int(cls[idx])
            label = str(names.get(class_id, classes[class_id] if class_id < len(classes) else f"class_{class_id}"))
            export_class_id = classes.index(label) if label in classes else min(class_id, len(classes) - 1)
            detections.append(
                Detection(
                    label=label,
                    class_id=export_class_id,
                    confidence=float(conf[idx]),
                    bbox_xyxy=tuple(float(value) for value in coords),
                )
            )
        return detections


class YOLOWorldDetector(YOLOEDetector):
    """Backward-compatible wrapper for legacy YOLO-World checkpoints."""

    def __init__(self, model_name: str, image_size: int = DEFAULT_IMAGE_SIZE, device: str | None = None) -> None:
        try:
            from ultralytics import YOLOWorld
        except ImportError as exc:
            raise RuntimeError(
                "Auto-Labelling requires ultralytics. Install it with: pip install ultralytics"
            ) from exc

        self.model_name = model_name
        self.image_size = image_size
        self.device = device if device is not None else os.getenv("AUTO_LABEL_GPU_DEVICE", "0")
        self._model = YOLOWorld(model_name)
        self._classes: list[str] = []


def create_detector(model_name: str) -> YOLOEDetector:
    if "world" in model_name.lower():
        return YOLOWorldDetector(model_name)
    return YOLOEDetector(model_name)


_CAPTION_LABEL_STOPWORDS = {
    # structural / function words
    "a", "an", "and", "are", "as", "at", "be", "behind", "beside", "between", "by",
    "for", "from", "front", "in", "inside", "into", "is", "it", "its", "near",
    "next", "of", "on", "onto", "or", "over", "the", "their", "there", "this",
    "to", "under", "with", "within",
    # possessive pronouns
    "his", "her", "their", "my", "your", "our",
    # action/state verbs
    "wearing", "holding", "standing", "stands", "walking", "walks", "working",
    "works", "doing", "does", "looking", "looks", "moving", "moves", "using",
    "uses", "seen", "visible", "appears", "showing", "shows",
    # action/state-only blockers
    "seated", "focused", "remains", "movement", "setting", "postures",
    "interactions", "attention", "focus", "actions", "work", "workplace",
    # meta-caption terms
    "scene", "frame", "frames", "provided", "interval", "activity", "change",
    "static", "discernible", "observation", "temporal", "throughout", "another",
    "overall", "continuous", "largely", "several", "various", "many", "multiple",
    "some", "same", "different", "segment", "segments", "period", "recording",
    "video", "camera", "consistent", "meaningful", "sustained", "open-plan",
    # abstract/non-object
    "something", "what", "background", "environment", "area", "positions",
    "level", "state", "interaction", "posture", "hand", "hands", "arm", "arms",
    "mouth", "head", "position", "left", "right", "first", "second", "third",
    "one", "two", "three", "exposed", "industrial",
}

_CAPTION_META_PHRASES = {
    "provided frames", "scene remains", "no discernible", "no change",
    "remains static", "remains largely", "no visible", "no activity",
    "throughout the", "across the", "temporal segment", "meaningful temporal",
    "no meaningful", "consistent and", "consistent state", "entire period",
    "static recording", "static office", "office scene",
}

_CAPTION_CANONICAL_MAP: dict[str, str] = {
    "man": "person",
    "woman": "person",
    "individual": "person",
    "guy": "person",
    "boy": "person",
    "girl": "person",
    "men": "person",
    "women": "person",
    "individuals": "person",
    "seated person": "person",
    "primary individual": "person",
    "three individuals": "person",
    "other two individuals": "person",
    "three men": "person",
    "first person": "person",
    "third person": "person",
    "screen": "monitor",
    "laptop screen": "laptop",
    "open laptop screen": "laptop",
    "boxes": "cardboard box",
    "cardboard boxes": "cardboard box",
    "desks": "desk",
    "their desks": "desk",
    "laptops": "laptop",
    "their laptop": "laptop",
    "his laptop": "laptop",
}

_nlp = None


def _get_spacy_nlp():
    """Lazy-load spaCy English model. Returns None if unavailable."""
    global _nlp
    if _nlp is not None:
        return None if _nlp is False else _nlp
    try:
        import spacy
        _nlp = spacy.load("en_core_web_sm")
        return _nlp
    except (ImportError, OSError):
        _nlp = False
        return None


def _extract_labels_spacy(nlp, caption: str) -> list[str]:
    """Extract candidate object labels using spaCy noun chunks."""
    doc = nlp(caption)
    labels: list[str] = []
    for chunk in doc.noun_chunks:
        text = chunk.text.lower().strip()
        text = re.sub(
            r"^(a |an |the |some |several |multiple |another |this |that |these |those "
            r"|his |her |their |my |your |our )+",
            "", text,
        )
        text = text.strip()
        if not text or len(text.split()) > 3:
            continue
        tokens = text.split()
        if all(t in _CAPTION_LABEL_STOPWORDS for t in tokens):
            continue
        if any(t in _CAPTION_LABEL_STOPWORDS for t in tokens) and len(tokens) <= 2:
            continue
        labels.append(text)
    return labels


def _extract_labels_regex(caption: str) -> list[str]:
    """Fallback regex-based label extraction when spaCy is unavailable."""
    tokens = [token for token in re.split(r"[^a-zA-Z0-9]+", caption.lower()) if token]
    labels: list[str] = []
    phrase: list[str] = []

    def flush() -> None:
        nonlocal phrase
        if phrase:
            label = " ".join(phrase[-3:])
            if label:
                labels.append(label)
            phrase = []

    for token in tokens:
        if token in _CAPTION_LABEL_STOPWORDS or token.isdigit():
            flush()
            continue
        phrase.append(token)
        if len(phrase) >= 3:
            flush()
    flush()
    return labels


def _canonicalize_label(label: str) -> str:
    """Apply canonical mapping and pattern-based normalization."""
    if label in _CAPTION_CANONICAL_MAP:
        return _CAPTION_CANONICAL_MAP[label]
    parts = label.split()
    # Normalize "<color> shirt" and "<color> <color> shirt" -> "shirt"
    if parts and parts[-1] == "shirt" and len(parts) >= 2:
        return "shirt"
    # Simple plural: single word ending in 's' (but not 'ss')
    if len(parts) == 1 and label.endswith("s") and not label.endswith("ss"):
        singular = label[:-1]
        if singular in _CAPTION_CANONICAL_MAP:
            return _CAPTION_CANONICAL_MAP[singular]
        return singular
    return label


def _is_meta_phrase(label: str) -> bool:
    """Return True if label is a meta-caption phrase that should be rejected."""
    label_lower = label.lower()
    return any(phrase in label_lower for phrase in _CAPTION_META_PHRASES)


def _is_valid_label(label: str) -> bool:
    """Return True if label looks like a valid detector object class."""
    if not label or len(label) < 2:
        return False
    if len(label.split()) > 4:
        return False
    if len(label) <= 3 and " " not in label:
        return False
    tokens = label.split()
    if all(t in _CAPTION_LABEL_STOPWORDS for t in tokens):
        return False
    return True


def extract_caption_labels(caption: str, max_labels: int = 8) -> list[str]:
    """Extract object-like detector labels from a caption when no manual prompt is given."""
    nlp = _get_spacy_nlp()
    if nlp is not None:
        labels = _extract_labels_spacy(nlp, caption)
    else:
        labels = _extract_labels_regex(caption)

    labels = [_canonicalize_label(label) for label in labels]
    labels = [label for label in labels if not _is_meta_phrase(label)]
    labels = [label for label in labels if _is_valid_label(label)]

    seen: set[str] = set()
    deduped: list[str] = []
    for label in labels:
        if label not in seen:
            seen.add(label)
            deduped.append(label)
    return deduped[:max_labels]


def parse_label_prompt(prompt: str) -> list[str]:
    """Convert a detector prompt into YOLOE class labels."""
    labels = [
        part.strip()
        for part in re.split(r"[,;\n]+", prompt)
        if part.strip()
    ]
    return labels


class AutoLabelJob:
    """Autonomous queue-backed labelling job for one video or RTSP session."""

    def __init__(
        self,
        mode: str,
        job_id: str,
        config: AutoLabelConfig,
        detector_factory: Optional[Callable[[str], YOLOEDetector]] = None,
        queue_size: int = DEFAULT_QUEUE_SIZE,
        dataset_root: Path = DATASET_ROOT,
    ) -> None:
        self.mode = mode
        self.job_id = job_id
        self.config = config
        self.prompt_classes = parse_label_prompt(config.prompt)
        self.classes = list(self.prompt_classes)
        self.dataset_dir = dataset_root / mode / job_id
        self.images_dir = self.dataset_dir / "images"
        self.labels_dir = self.dataset_dir / "labels"
        self.overlays_dir = self.dataset_dir / "overlays"
        self.metadata_path = self.dataset_dir / "annotations.jsonl"
        self.data_yaml_path = self.dataset_dir / "data.yaml"

        self._detector_factory = detector_factory or create_detector
        self._queue: queue.Queue[AutoLabelFrame] = queue.Queue(maxsize=queue_size)
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, name=f"auto-label-{mode}-{job_id}", daemon=True)

        self.status = "idle"
        self.frames_labelled = 0
        self.frames_dropped = 0
        self.chunks_enqueued = 0
        self.latest_overlay_path: str | None = None
        self.started_at: datetime | None = None
        self.finished_at: datetime | None = None
        self.expires_at: datetime | None = None
        self.last_error: str | None = None

    def start(self) -> None:
        with self._lock:
            if self.status in {"active", "draining"}:
                return
            self.dataset_dir.mkdir(parents=True, exist_ok=True)
            self.images_dir.mkdir(parents=True, exist_ok=True)
            self.labels_dir.mkdir(parents=True, exist_ok=True)
            self.overlays_dir.mkdir(parents=True, exist_ok=True)
            self._write_data_yaml()
            self.status = "active"
            self.started_at = datetime.now(timezone.utc)
            self.expires_at = (
                self.started_at + timedelta(minutes=self.config.duration_minutes)
                if self.config.schedule_mode == "duration"
                else None
            )
        self._thread.start()

    def stop(self, drain: bool = True) -> None:
        with self._lock:
            if self.status == "active":
                self.status = "draining" if drain else "done"
        self._stop_event.set()
        if not drain:
            self._clear_queue()

    def enqueue_chunk(
        self,
        frames: Iterable[np.ndarray],
        segment_seq: int,
        caption: str,
        frame_seq_start: int,
        source: str,
    ) -> bool:
        if not self.is_accepting():
            return False

        captured_at = datetime.now(timezone.utc)
        accepted = False
        for offset, frame in enumerate(frames):
            item = AutoLabelFrame(
                frame=frame.copy(),
                segment_seq=segment_seq,
                frame_seq=frame_seq_start + offset,
                frame_offset=offset,
                caption=caption,
                source=source,
                captured_at=captured_at,
            )
            self._put_drop_oldest(item)
            accepted = True

        if accepted:
            with self._lock:
                self.chunks_enqueued += 1
        return accepted

    def is_accepting(self) -> bool:
        with self._lock:
            if self.status != "active":
                return False
            if self.expires_at is not None and datetime.now(timezone.utc) >= self.expires_at:
                self.status = "draining"
                self._stop_event.set()
                return False
            return True

    def join(self, timeout: float | None = None) -> None:
        if self._thread.is_alive():
            self._thread.join(timeout=timeout)

    def snapshot(self) -> AutoLabelStatus:
        with self._lock:
            remaining = None
            if self.status == "active" and self.expires_at is not None:
                remaining = max(0.0, (self.expires_at - datetime.now(timezone.utc)).total_seconds())
            return AutoLabelStatus(
                status=self.status,
                dataset_path=str(self.dataset_dir) if self.started_at else None,
                latest_overlay_path=self.latest_overlay_path,
                frames_labelled=self.frames_labelled,
                frames_dropped=self.frames_dropped,
                chunks_enqueued=self.chunks_enqueued,
                remaining_seconds=remaining,
                started_at=self.started_at,
                finished_at=self.finished_at,
                last_error=self.last_error,
            )

    def _put_drop_oldest(self, item: AutoLabelFrame) -> None:
        while True:
            try:
                self._queue.put_nowait(item)
                return
            except queue.Full:
                try:
                    self._queue.get_nowait()
                    self._queue.task_done()
                    with self._lock:
                        self.frames_dropped += 1
                except queue.Empty:
                    continue

    def _run(self) -> None:
        try:
            detector = self._detector_factory(self.config.model)
            while True:
                if self._should_finish():
                    break
                try:
                    item = self._queue.get(timeout=0.2)
                except queue.Empty:
                    self.is_accepting()
                    continue
                try:
                    classes = self._classes_for_item(item)
                    detections = detector.detect(item.frame, classes, self.config.confidence)
                    detections = self._remap_detections(detections)
                    self._write_frame_outputs(item, detections, classes)
                    with self._lock:
                        self.frames_labelled += 1
                finally:
                    self._queue.task_done()
        except Exception as exc:
            with self._lock:
                self.status = "error"
                self.last_error = str(exc)
                self.finished_at = datetime.now(timezone.utc)
            return

        with self._lock:
            self.status = "done"
            self.finished_at = datetime.now(timezone.utc)

    def _should_finish(self) -> bool:
        with self._lock:
            if self.status == "done":
                return True
            if self.status == "active" and self.expires_at and datetime.now(timezone.utc) >= self.expires_at:
                self.status = "draining"
                self._stop_event.set()
            return self._stop_event.is_set() and self._queue.empty()

    def _clear_queue(self) -> None:
        while True:
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except queue.Empty:
                break

    def _classes_for_item(self, item: AutoLabelFrame) -> list[str]:
        classes = self.prompt_classes or extract_caption_labels(item.caption) or ["object"]
        self._register_classes(classes)
        return classes

    def _register_classes(self, classes: Iterable[str]) -> None:
        changed = False
        with self._lock:
            for label in classes:
                if label not in self.classes:
                    self.classes.append(label)
                    changed = True
        if changed:
            self._write_data_yaml()

    def _remap_detections(self, detections: list[Detection]) -> list[Detection]:
        remapped: list[Detection] = []
        for detection in detections:
            class_id = self.classes.index(detection.label) if detection.label in self.classes else detection.class_id
            remapped.append(
                Detection(
                    label=detection.label,
                    class_id=class_id,
                    confidence=detection.confidence,
                    bbox_xyxy=detection.bbox_xyxy,
                )
            )
        return remapped

    def _write_frame_outputs(self, item: AutoLabelFrame, detections: list[Detection], classes: list[str]) -> None:
        stem = f"segment_{item.segment_seq:06d}_frame_{item.frame_seq:06d}"
        image_path = self.images_dir / f"{stem}.jpg"
        label_path = self.labels_dir / f"{stem}.txt"
        overlay_path = self.overlays_dir / f"{stem}.jpg"

        cv2.imwrite(str(image_path), item.frame)
        label_path.write_text(self._to_yolo_labels(item.frame, detections), encoding="utf-8")
        cv2.imwrite(str(overlay_path), self._draw_overlay(item.frame, detections))

        metadata = {
            "mode": self.mode,
            "job_id": self.job_id,
            "source": item.source,
            "segment_seq": item.segment_seq,
            "frame_seq": item.frame_seq,
            "frame_offset": item.frame_offset,
            "caption": item.caption,
            "label_prompt": self.config.prompt,
            "schedule_mode": self.config.schedule_mode,
            "classes": classes,
            "class_registry": self.classes,
            "detector_model": self.config.model,
            "confidence_threshold": self.config.confidence,
            "captured_at": item.captured_at.isoformat(),
            "image_path": str(image_path),
            "label_path": str(label_path),
            "overlay_path": str(overlay_path),
            "detections": [
                {
                    "label": detection.label,
                    "class_id": detection.class_id,
                    "confidence": detection.confidence,
                    "bbox_xyxy": list(detection.bbox_xyxy),
                }
                for detection in detections
            ],
        }
        with self.metadata_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(metadata) + "\n")

        with self._lock:
            self.latest_overlay_path = str(overlay_path)

    def _to_yolo_labels(self, frame: np.ndarray, detections: list[Detection]) -> str:
        height, width = frame.shape[:2]
        lines: list[str] = []
        for detection in detections:
            x1, y1, x2, y2 = clamp_bbox(detection.bbox_xyxy, width, height)
            box_width = max(0.0, x2 - x1)
            box_height = max(0.0, y2 - y1)
            if box_width <= 0 or box_height <= 0:
                continue
            x_center = (x1 + x2) / 2 / width
            y_center = (y1 + y2) / 2 / height
            lines.append(
                f"{detection.class_id} {x_center:.6f} {y_center:.6f} "
                f"{box_width / width:.6f} {box_height / height:.6f}"
            )
        return "\n".join(lines) + ("\n" if lines else "")

    def _draw_overlay(self, frame: np.ndarray, detections: list[Detection]) -> np.ndarray:
        overlay = frame.copy()
        height, width = overlay.shape[:2]
        for detection in detections:
            x1, y1, x2, y2 = clamp_bbox(detection.bbox_xyxy, width, height)
            if x2 <= x1 or y2 <= y1:
                continue
            start = (int(round(x1)), int(round(y1)))
            end = (int(round(x2)), int(round(y2)))
            cv2.rectangle(overlay, start, end, (62, 207, 142), 2)
            label = f"{detection.label} {detection.confidence:.2f}"
            cv2.putText(
                overlay,
                label,
                (start[0], max(16, start[1] - 6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (62, 207, 142),
                1,
                cv2.LINE_AA,
            )
        return overlay

    def _write_data_yaml(self) -> None:
        names = "\n".join(f"  {idx}: {label}" for idx, label in enumerate(self.classes))
        self.data_yaml_path.write_text(
            f"path: {self.dataset_dir}\ntrain: images\nval: images\nnames:\n{names}\n",
            encoding="utf-8",
        )


def clamp_bbox(bbox: tuple[float, float, float, float], width: int, height: int) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = bbox
    return (
        min(max(x1, 0.0), float(width)),
        min(max(y1, 0.0), float(height)),
        min(max(x2, 0.0), float(width)),
        min(max(y2, 0.0), float(height)),
    )
