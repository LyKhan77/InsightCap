from __future__ import annotations

from backend.core.config import SamplerConfig
from backend.core.video.reader import VideoReader


class FrameSampler:
    """Samples frames from a VideoReader according to SamplerConfig.

    Captures 1 frame every `frame_interval` native frames (e.g. every 10th
    frame on a 30fps video = 3 captures/sec), capped at `max_frames`.
    """

    def __init__(self, config: SamplerConfig | None = None) -> None:
        self.config = config or SamplerConfig()

    def sample(self, reader: VideoReader) -> list:
        """Return a list of BGR frames sampled from the video."""
        total_frames = reader.frame_count
        video_fps = reader.fps

        if total_frames <= 0 or video_fps <= 0:
            return []

        indices = self._compute_indices(total_frames)
        frames = []
        for idx in indices:
            frame = reader.read_frame(idx)
            if frame is not None:
                frames.append(frame)
        return frames

    def _compute_indices(self, total_frames: int) -> list[int]:
        interval = max(1, self.config.frame_interval)
        indices = list(range(0, total_frames, interval))
        return indices[: self.config.max_frames]
