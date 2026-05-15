# RTSP Segment Live Analysis

## Summary

- Change RTSP Live Analysis from one caption per sampled frame to one caption per 10 sampled-frame segment.
- Send the 10 current sampled frames as one multi-image vLLM request.
- Use the previous segment caption as text context for temporal continuity.

## Implementation

- Add multi-frame inference support to `CaptionBackend` and `VLLMBackend`.
- Add a live segment prompt builder that describes a 10-frame temporal segment and includes previous segment observations.
- Buffer sampled RTSP frames inside `RtspSession` until 10 frames are ready, then emit one existing `caption` WebSocket event with extra segment metadata.
- Keep preview capture independent from inference so MJPEG preview remains responsive.
- Configure vLLM with `--limit-mm-per-prompt.image 10`.

## Event Contract

RTSP WebSocket `caption` events keep the existing `caption` field and add:

- `sampled_frame_count`
- `frame_seq_start`
- `frame_seq_end`
- `captured_at`
- `processed_at`
- `lag_ms`

## Verification

- Unit tests cover multi-image vLLM payloads.
- Unit tests cover live segment prompt context.
- Unit tests cover RTSP segment buffering, delayed emission until 10 sampled frames, and previous segment caption context.
