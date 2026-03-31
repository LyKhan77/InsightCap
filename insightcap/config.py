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
    stream: bool = False  
    backend: str = "ollama"
    max_tokens: int = 1024
    no_think: bool = True  
    temporal_context_frames: int = 3  
    frame_prompt: str = (
        "Describe what is happening in this video frame. "
        "Be concise, factual, and specific. "
        "Only describe what is clearly visible."
    )
    summary_prompt: str = (
        "You are given frame-by-frame descriptions from a video.\n"
        "If the request below is a question, answer it directly and precisely.\n"
        "If the request asks for a summary, write a coherent narrative.\n"
        "Be factual and avoid guessing anything not described."
    )
