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
        """Convert a BGR numpy frame to JPEG bytes for VLM backends."""
        pil_image = self.frame_to_pil(frame)
        buf = io.BytesIO()
        pil_image.save(buf, format=format)
        return buf.getvalue()

    def build_frame_message(self, frame: np.ndarray) -> dict:
        """Build a chat message dict for a single frame."""
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
                f"{self.frame_prompt}\n\n"
                f"Previous frame descriptions:\n{context_lines}\n\n"
                f"Describe frame {frame_num} of {total_frames}."
            )
        else:
            prompt = f"{self.frame_prompt}\n\nDescribe frame 1 of {total_frames}."
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

    def build_live_segment_prompt(
        self,
        previous_captions: list[str],
        segment_num: int,
        source_label: str,
        sampled_frame_count: int,
    ) -> str:
        """Build a prompt for a live segment made from multiple sampled frames."""
        base = (
            f"Source: {source_label}\n"
            f"Analyze these {sampled_frame_count} live camera frames as one temporal segment "
            f"#{segment_num}. Describe the meaningful activity across the segment, not each "
            f"frame separately. {self.frame_prompt}"
        )
        if not previous_captions:
            return base

        context_lines = "\n".join(
            f"Previous segment {i + 1}: {caption}"
            for i, caption in enumerate(previous_captions)
        )
        return (
            f"Source: {source_label}\n"
            f"Previous segment observations:\n{context_lines}\n\n"
            f"Analyze these {sampled_frame_count} live camera frames as one temporal segment "
            f"#{segment_num}. Use the previous segment observations only for temporal context. "
            f"Describe the meaningful activity across the segment, not each frame separately. "
            f"{self.frame_prompt}"
        )

    def build_short_video_prompt(self, sampled_frame_count: int) -> str:
        """Build a prompt for short uploaded videos processed as one segment."""
        return (
            f"Analyze these {sampled_frame_count} sampled video frames as one short video segment. "
            "Describe the most meaningful activity across the full clip, not frame-by-frame. "
            f"{self.frame_prompt}"
        )

    def build_summary_message(self, frame_captions: list[str], summary_prompt: str) -> dict:
        """Build the chat message for summarizing all frame captions."""
        captions_text = "\n".join(
            f"Frame {i + 1}: {caption}" for i, caption in enumerate(frame_captions)
        )
        prompt = (
            f"{summary_prompt}\n\n"
            f"Frame-by-frame descriptions:\n{captions_text}\n\n"
            f"Answer the question above based on the frame descriptions."
        )
        return {
            "role": "user",
            "content": prompt,
        }
