from __future__ import annotations

import base64
from typing import Any, Iterator

import numpy as np

from insightcap.config import InferenceConfig
from insightcap.inference.base import CaptionBackend
from insightcap.prompt.builder import PromptBuilder


class VLLMBackend(CaptionBackend):
    """Inference backend using a vLLM OpenAI-compatible server."""

    def __init__(self, config: InferenceConfig | None = None, client: Any | None = None) -> None:
        self.config = config or InferenceConfig()
        self._builder = PromptBuilder(frame_prompt=self.config.frame_prompt)
        self._client = client or self._build_client()

    def _build_client(self) -> Any:
        try:
            from openai import OpenAI
        except ImportError as e:
            raise ImportError(
                "openai package not found. Install it with: pip install openai\n"
                "vLLM itself runs in Docker; the API process only needs the OpenAI client."
            ) from e

        return OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.vllm_base_url,
        )

    @staticmethod
    def _message_content(response: Any) -> str:
        choices = getattr(response, "choices", None) or []
        if not choices:
            return ""
        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", "") if message is not None else ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(
                item.get("text", "") for item in content if isinstance(item, dict)
            )
        return content or ""

    @staticmethod
    def _chunk_content(chunk: Any) -> str:
        choices = getattr(chunk, "choices", None) or []
        if not choices:
            return ""
        delta = getattr(choices[0], "delta", None)
        content = getattr(delta, "content", "") if delta is not None else ""
        return content or ""

    def _extra_body(self) -> dict[str, Any]:
        return {"top_k": self.config.top_k}

    def _create_completion(
        self,
        messages: list[dict[str, Any]],
        stream: bool,
    ) -> Any:
        return self._client.chat.completions.create(
            model=self.config.model_id,
            messages=messages,
            stream=stream,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            presence_penalty=self.config.presence_penalty,
            extra_body=self._extra_body(),
        )

    def _image_data_url(self, frame: np.ndarray) -> str:
        image_bytes = self._builder.frame_to_bytes(frame)
        encoded = base64.b64encode(image_bytes).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"

    def generate_for_frame(self, frame: np.ndarray, prompt: str) -> Iterator[str]:
        message = {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": self._image_data_url(frame)},
                },
            ],
        }
        response = self._create_completion([message], stream=self.config.stream)
        if self.config.stream:
            for chunk in response:
                content = self._chunk_content(chunk)
                if content:
                    yield content
        else:
            content = self._message_content(response)
            if content:
                yield content

    def summarize(self, frame_captions: list[str], summary_prompt: str) -> Iterator[str]:
        message = self._builder.build_summary_message(frame_captions, summary_prompt)
        response = self._create_completion([message], stream=self.config.stream)
        if self.config.stream:
            for chunk in response:
                content = self._chunk_content(chunk)
                if content:
                    yield content
        else:
            content = self._message_content(response)
            if content:
                yield content
