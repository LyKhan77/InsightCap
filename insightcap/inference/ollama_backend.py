from __future__ import annotations

from typing import Iterator

import numpy as np

try:
    import ollama
except ImportError as e:
    raise ImportError(
        "ollama package not found. Install it with: pip install ollama\n"
        "Also ensure Ollama is running: https://ollama.com/download"
    ) from e

from insightcap.config import InferenceConfig
from insightcap.inference.base import CaptionBackend
from insightcap.prompt.builder import PromptBuilder

# /no_think prefix disables Qwen3's internal reasoning chain,
# returning answers immediately without the <think>...</think> block.
_NO_THINK_PREFIX = "/no_think "


class OllamaBackend(CaptionBackend):
    """Inference backend using the local Ollama server with qwen3.5:0.8b."""

    def __init__(self, config: InferenceConfig | None = None) -> None:
        self.config = config or InferenceConfig()
        self._builder = PromptBuilder(frame_prompt=self.config.frame_prompt)

    def _prefix(self, text: str) -> str:
        """Optionally prepend /no_think to suppress Qwen3 thinking mode."""
        if self.config.no_think:
            return _NO_THINK_PREFIX + text
        return text

    @staticmethod
    def _content(chunk) -> str:
        """Extract text content from an ollama response chunk.

        Handles both the object-based API (ollama >= 0.2) and legacy dict format.
        """
        if hasattr(chunk, "message"):
            return chunk.message.content or ""
        if isinstance(chunk, dict):
            msg = chunk.get("message", {})
            return (msg.get("content") or "") if isinstance(msg, dict) else ""
        return ""

    def generate_for_frame(self, frame: np.ndarray, prompt: str) -> Iterator[str]:
        """Stream caption tokens for a single BGR video frame."""
        image_bytes = self._builder.frame_to_bytes(frame)
        response = ollama.chat(
            model=self.config.model_id,
            messages=[
                {
                    "role": "user",
                    "content": self._prefix(prompt),
                    "images": [image_bytes],
                }
            ],
            stream=self.config.stream,
            think=False,
            options={"num_predict": self.config.max_tokens},
        )
        if self.config.stream:
            for chunk in response:
                content = self._content(chunk)
                if content:
                    yield content
        else:
            yield self._content(response)

    def summarize(self, frame_captions: list[str], summary_prompt: str) -> Iterator[str]:
        """Stream a summary given ordered per-frame caption strings."""
        message = self._builder.build_summary_message(frame_captions, summary_prompt)
        message["content"] = self._prefix(message["content"])
        response = ollama.chat(
            model=self.config.model_id,
            messages=[message],
            stream=self.config.stream,
            think=False,
            options={"num_predict": self.config.max_tokens},
        )
        if self.config.stream:
            for chunk in response:
                content = self._content(chunk)
                if content:
                    yield content
        else:
            yield self._content(response)
