from __future__ import annotations

import os

import cv2
import numpy as np


class LiveStreamReader:
    """Sequential OpenCV reader for RTSP and other live stream URLs."""

    def __init__(
        self,
        url: str,
        open_timeout_ms: int = 5000,
        read_timeout_ms: int = 15000,
    ) -> None:
        self.url = url
        self.open_timeout_ms = open_timeout_ms
        self.read_timeout_ms = read_timeout_ms
        self._cap: cv2.VideoCapture | None = None

    def open(self) -> None:
        self.close()
        self._prepare_rtsp_transport()
        self._cap = self._open_capture()
        if not self._cap.isOpened():
            raise IOError(f"Cannot open live stream: {self.url}")

    def _open_capture(self) -> cv2.VideoCapture:
        attempts = []
        params = self._capture_params()
        if params:
            attempts.append((self.url, cv2.CAP_FFMPEG, params))
        attempts.append((self.url, cv2.CAP_FFMPEG))
        attempts.append((self.url,))

        last_capture: cv2.VideoCapture | None = None
        for args in attempts:
            capture = cv2.VideoCapture(*args)
            if capture.isOpened():
                return capture
            capture.release()
            last_capture = capture

        return last_capture or cv2.VideoCapture()

    def _prepare_rtsp_transport(self) -> None:
        if not self.url.lower().startswith("rtsp://"):
            return
        os.environ.setdefault(
            "OPENCV_FFMPEG_CAPTURE_OPTIONS",
            "rtsp_transport;tcp|stimeout;15000000|max_delay;500000",
        )

    def _capture_params(self) -> list[int]:
        params: list[int] = []
        if hasattr(cv2, "CAP_PROP_OPEN_TIMEOUT_MSEC"):
            params.extend([cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, int(self.open_timeout_ms)])
        if hasattr(cv2, "CAP_PROP_READ_TIMEOUT_MSEC"):
            params.extend([cv2.CAP_PROP_READ_TIMEOUT_MSEC, int(self.read_timeout_ms)])
        return params

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
