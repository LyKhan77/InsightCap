from __future__ import annotations

from insightcap.config import InferenceConfig
from insightcap.inference.base import CaptionBackend


def get_backend(config: InferenceConfig | None = None) -> CaptionBackend:
    """Return the appropriate CaptionBackend for the given config."""
    config = config or InferenceConfig()

    if config.backend == "ollama":
        from insightcap.inference.ollama_backend import OllamaBackend
        return OllamaBackend(config)

    if config.backend == "vllm":
        raise NotImplementedError(
            "vLLM backend is not yet implemented. "
            "It is reserved for Phase 2 production deployment on Linux + NVIDIA GPU."
        )

    raise ValueError(f"Unknown backend: {config.backend!r}. Valid options: 'ollama', 'vllm'.")
