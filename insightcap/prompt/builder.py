from __future__ import annotations

import io

import cv2
import numpy as np
from PIL import Image


class PromptBuilder:
    """Converts BGR frames to PIL images and assembles per-frame prompt text."""

    def __init__(self, frame_prompt: str | None = None) -> None:
        self.frame_prompt = frame_prompt or (
            "Describe what is happening in this video frame. "
            "Be concise and factual. Only describe what is clearly visible."
        )

    def frame_to_pil(self, frame: np.ndarray) -> Image.Image:
        """Convert a BGR numpy frame to a PIL RGB image."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)

    def frame_to_bytes(self, frame: np.ndarray, format: str = "JPEG") -> bytes:
        """Convert a BGR numpy frame to JPEG bytes for Ollama."""
        pil_image = self.frame_to_pil(frame)
        buf = io.BytesIO()
        pil_image.save(buf, format=format)
        return buf.getvalue()

    def build_frame_message(self, frame: np.ndarray) -> dict:
        """Build the Ollama chat message dict for a single frame."""
        return {
            "role": "user",
            "content": self.frame_prompt,
            "images": [self.frame_to_bytes(frame)],
        }

    def build_frame_message_with_context(
        self,
        frame,
        previous_captions: list[str],
        frame_num: int,
        total_frames: int,
    ) -> dict:
        """Build a context-aware frame message including previous captions."""
        if previous_captions:
            context_lines = "\n".join(
                f"Frame {frame_num - len(previous_captions) + i}: {c}"
                for i, c in enumerate(previous_captions)
            )
            prompt = (
                f"Previous frame descriptions:\n{context_lines}\n\n"
                f"Now describe frame {frame_num} of {total_frames}, "
                f"continuing the narrative. {self.frame_prompt}"
            )
        else:
            prompt = f"Describe frame 1 of {total_frames}. {self.frame_prompt}"
        return {
            "role": "user",
            "content": prompt,
            "images": [self.frame_to_bytes(frame)],
        }

    def build_live_frame_prompt(
        self,
        previous_captions: list[str],
        frame_num: int,
        source_label: str,
    ) -> str:
        """Build a prompt for a live frame without assuming a finite video."""
        if previous_captions:
            context_lines = "\n".join(
                f"Recent observation {i + 1}: {caption}"
                for i, caption in enumerate(previous_captions)
            )
            return (
                f"Source: {source_label}\n"
                f"Recent observations:\n{context_lines}\n\n"
                f"Now describe the latest live camera frame #{frame_num}. "
                f"Continue the monitoring narrative. {self.frame_prompt}"
            )
        return (
            f"Source: {source_label}\n"
            f"Describe the latest live camera frame #{frame_num}. "
            f"Continue the monitoring narrative. {self.frame_prompt}"
        )

    def build_summary_message(self, frame_captions: list[str], summary_prompt: str) -> dict:
        """Build the Ollama chat message for summarizing all frame captions."""
        captions_text = "\n".join(
            f"Frame {i + 1}: {caption}" for i, caption in enumerate(frame_captions)
        )
        return {
            "role": "user",
            "content": f"{summary_prompt}\n\n{captions_text}",
        }
