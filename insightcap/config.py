from dataclasses import dataclass


@dataclass
class SamplerConfig:
    # Capture 1 frame every N frames of the native video fps.
    # e.g. frame_interval=10 on a 30fps video → 3 captures/sec.
    frame_interval: int = 10
    max_frames: int = 60  # hard stop to prevent runaway on long videos


@dataclass
class InferenceConfig:
    model_id: str = "qwen3.5:0.8b"
    stream: bool = False  # Non-streaming is reliable; Qwen3.5 thinking chunks cause empty content in stream mode
    backend: str = "ollama"
    max_tokens: int = 1024
    no_think: bool = True  # Disable Qwen3 thinking mode for faster responses
    temporal_context_frames: int = 3  # how many previous captions to include as context
    frame_prompt: str = (
        "Describe what is happening in this video frame, continuing the narrative. "
        "Be concise and specific. Only describe what is clearly visible."
    )
    summary_prompt: str = (
        "You are given a sequence of frame-by-frame descriptions from a video. "
        "Write a coherent 2-3 sentence narrative of the full video — "
        "what happens, in what order, and what the video is about. "
        "Be factual and avoid guessing anything not described."
    )
