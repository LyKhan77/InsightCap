from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator

import numpy as np


class CaptionBackend(ABC):
    """Abstract base class for caption inference backends.

    vLLM is the supported backend for current development.
    """

    @abstractmethod
    def generate_for_frame(self, frame: np.ndarray, prompt: str) -> Iterator[str]:
        """Stream caption tokens for a single video frame.

        Args:
            frame: BGR numpy array from OpenCV.
            prompt: Instruction text for the model.

        Yields:
            Text chunks as they are streamed from the model.
        """

    @abstractmethod
    def summarize(self, frame_captions: list[str], summary_prompt: str) -> Iterator[str]:
        """Stream a summary caption given per-frame captions as text.

        Args:
            frame_captions: Ordered list of per-frame caption strings.
            summary_prompt: Instruction text for the summarization call.

        Yields:
            Text chunks as they are streamed from the model.
        """
