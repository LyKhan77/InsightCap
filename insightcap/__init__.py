"""InsightCap — video understanding and captioning engine."""

__all__ = ["CaptionPipeline", "CaptionResult"]


def __getattr__(name: str):
    if name in ("CaptionPipeline", "CaptionResult"):
        from insightcap.pipeline import CaptionPipeline, CaptionResult  # noqa: F401
        return {"CaptionPipeline": CaptionPipeline, "CaptionResult": CaptionResult}[name]
    raise AttributeError(f"module 'insightcap' has no attribute {name!r}")
