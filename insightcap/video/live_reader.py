from __future__ import annotations

import cv2
import numpy as np


class LiveStreamReader:
    """Sequential OpenCV reader for RTSP and other live stream URLs."""

    def __init__(
        self,
        url: str,
        open_timeout_ms: int = 5000,
        read_timeout_ms: int = 5000,
    ) -> None:
        self.url = url
        self.open_timeout_ms = open_timeout_ms
        self.read_timeout_ms = read_timeout_ms
        self._cap: cv2.VideoCapture | None = None

    def open(self) -> None:
        self._cap = cv2.VideoCapture(self.url)
        self._apply_timeouts()
        if not self._cap.isOpened():
            raise IOError(f"Cannot open live stream: {self.url}")

    def _apply_timeouts(self) -> None:
        if self._cap is None:
            return
        if hasattr(cv2, "CAP_PROP_OPEN_TIMEOUT_MSEC"):
            self._cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, float(self.open_timeout_ms))
        if hasattr(cv2, "CAP_PROP_READ_TIMEOUT_MSEC"):
            self._cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, float(self.read_timeout_ms))

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __enter__(self) -> LiveStreamReader:
        self.open()
        return self

    def __exit__(self, *_) -> None:
        self.close()

    def _require_open(self) -> None:
        if self._cap is None or not self._cap.isOpened():
            raise RuntimeError("LiveStreamReader is not open. Call open() first.")

    @property
    def fps(self) -> float:
        self._require_open()
        return self._cap.get(cv2.CAP_PROP_FPS)  # type: ignore[union-attr]

    @property
    def width(self) -> int:
        self._require_open()
        return int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # type: ignore[union-attr]

    @property
    def height(self) -> int:
        self._require_open()
        return int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # type: ignore[union-attr]

    def read(self) -> np.ndarray | None:
        """Read the next frame from the live stream."""
        self._require_open()
        ret, frame = self._cap.read()  # type: ignore[union-attr]
        if not ret:
            return None
        return frame
