from __future__ import annotations

import cv2
import numpy as np


class VideoReader:
    """Thin wrapper around cv2.VideoCapture for reading local video files."""

    def __init__(self, path: str) -> None:
        self.path = path
        self._cap: cv2.VideoCapture | None = None

    def open(self) -> None:
        self._cap = cv2.VideoCapture(self.path)
        if not self._cap.isOpened():
            raise IOError(f"Cannot open video: {self.path}")

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __enter__(self) -> VideoReader:
        self.open()
        return self

    def __exit__(self, *_) -> None:
        self.close()

    def _require_open(self) -> None:
        if self._cap is None or not self._cap.isOpened():
            raise RuntimeError("VideoReader is not open. Call open() first.")

    @property
    def fps(self) -> float:
        self._require_open()
        return self._cap.get(cv2.CAP_PROP_FPS)  # type: ignore[union-attr]

    @property
    def frame_count(self) -> int:
        self._require_open()
        return int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))  # type: ignore[union-attr]

    @property
    def width(self) -> int:
        self._require_open()
        return int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # type: ignore[union-attr]

    @property
    def height(self) -> int:
        self._require_open()
        return int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # type: ignore[union-attr]

    @property
    def duration_seconds(self) -> float:
        fps = self.fps
        if fps <= 0:
            return 0.0
        return self.frame_count / fps

    def read_frame(self, frame_index: int) -> np.ndarray | None:
        """Seek to frame_index and return the BGR frame, or None on failure."""
        self._require_open()
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, float(frame_index))  # type: ignore[union-attr]
        ret, frame = self._cap.read()  # type: ignore[union-attr]
        if not ret:
            return None
        return frame
