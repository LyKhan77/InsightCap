from __future__ import annotations

from insightcap.config import InferenceConfig
from insightcap.inference.base import CaptionBackend


def get_backend(config: InferenceConfig | None = None) -> CaptionBackend:
    """Return the appropriate CaptionBackend for the given config."""
    config = config or InferenceConfig()

    if config.backend == "vllm":
        from insightcap.inference.vllm_backend import VLLMBackend
        return VLLMBackend(config)

    raise ValueError(f"Unknown backend: {config.backend!r}. Valid options: 'vllm'.")
