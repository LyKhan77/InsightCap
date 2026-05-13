"""CLI entrypoint for InsightCap.

Usage:
    python -m backend.core.cli VIDEO_PATH [OPTIONS]
"""

import json
import sys

import click

from backend.core.config import InferenceConfig, SamplerConfig
from backend.core.pipeline import CaptionPipeline


@click.command()
@click.argument("video_path", type=click.Path(exists=True))
@click.option("--frame-interval", default=10, show_default=True, help="Capture 1 frame every N native frames.")
@click.option("--max-frames", default=60, show_default=True, help="Maximum frames to process.")
@click.option("--model", default="qwen3.5:0.8b", show_default=True, help="vLLM served model name.")
@click.option("--verbose", is_flag=True, default=False, help="Show per-frame captions while processing.")
@click.option("--output", default=None, type=click.Path(), help="Save results to a JSON file.")
def caption(
    video_path: str,
    frame_interval: int,
    max_frames: int,
    model: str,
    verbose: bool,
    output: str,
) -> None:
    """Analyze a local video file and print a caption."""
    sampler_config = SamplerConfig(frame_interval=frame_interval, max_frames=max_frames)
    inference_config = InferenceConfig(model_id=model)

    pipeline = CaptionPipeline(
        sampler_config=sampler_config,
        inference_config=inference_config,
    )

    click.echo(f"Analyzing: {video_path}  [{model}]")
    if verbose:
        click.echo(f"frame-interval: {frame_interval}  |  max-frames: {max_frames}\n")

    def on_frame_start(idx: int, total: int) -> None:
        if verbose:
            click.echo(f"[Frame {idx + 1:>2}/{total}] ", nl=False)
            sys.stdout.flush()

    def on_frame_done(idx: int, frame_caption: str) -> None:
        if verbose:
            click.echo(frame_caption)

    result = pipeline.run(
        video_path,
        on_frame_start=on_frame_start,
        on_frame_done=on_frame_done,
    )

    click.echo(f"\n{'─' * 60}")
    click.echo("SUMMARY")
    click.echo("─" * 60)
    click.echo(result.caption)

    click.echo(
        f"\nFrames: {result.frame_count}  |  "
        f"Duration: {result.duration_seconds:.1f}s  |  "
        f"Device: {result.device_used}",
        err=True,
    )

    if output:
        data = {
            "video": video_path,
            "model": result.model_id,
            "device": result.device_used,
            "duration_seconds": result.duration_seconds,
            "frame_count": result.frame_count,
            "caption": result.caption,
            "frame_captions": result.frame_captions,
        }
        with open(output, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        click.echo(f"Results saved to: {output}", err=True)


def main() -> None:
    caption()


if __name__ == "__main__":
    main()
