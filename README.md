# InsightCap

Video understanding and captioning system powered by `qwen3.5:0.8b` via Ollama.

Analyzes a video file, generates per-frame captions with temporal context, and produces a coherent narrative summary — all streamed in real-time to the browser.

## Prerequisites

1. **Ollama** installed and running: https://ollama.com/download

2. Pull the model (~500MB):
   ```bash
   ollama pull qwen3.5:0.8b
   ```

3. Ensure Ollama server is running:
   ```bash
   ollama serve
   ```

## Setup

```bash
cd /path/to/video-captioning
python3 -m venv env
source env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Running

```bash
# Terminal 1: Start API server
uvicorn api.main:app --reload --port 6060

# Terminal 2: Start Web App
cd web && streamlit run app.py
```

Access the web app at **http://localhost:8501**

---

## Web Interface

Industrial dark-themed dual-panel UI:

- **Left panel — LIVE_STREAM**: Video player (autoplays and locks during analysis)
- **Right panel — LIVE_CAPTIONS**: Captions stream in real-time as frames are processed

**How it works:**
1. Upload a video in the sidebar
2. Select model (default: `qwen3.5:0.8b`)
3. Click `[ INITIATE_ANALYSIS ]`
4. Backend reads video metadata → frontend shows `INITIALIZING...`
5. Video autoplays + locks; captions stream in the right panel
6. Pipeline stops automatically when video duration is reached
7. Final narrative summary appears; video controls restored

No FPS or frame interval config needed — sampling is auto-computed from the video.

---

## CLI

```bash
# Basic caption (summary only)
python -m insightcap.cli path/to/video.mp4

# Verbose (per-frame + summary)
python -m insightcap.cli path/to/video.mp4 --verbose

# Custom model
python -m insightcap.cli path/to/video.mp4 --model qwen3.5:0.8b

# Save to JSON
python -m insightcap.cli path/to/video.mp4 --output result.json
```

---

## API

- Swagger UI: http://localhost:6060/docs
- Health check: http://localhost:6060/health

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Status + device info |
| `POST` | `/api/v1/analyze` | Upload video → full JSON result |
| `POST` | `/api/v1/analyze/stream` | Upload video → SSE streaming |

### curl Examples

```bash
# Non-streaming
curl -X POST http://localhost:6060/api/v1/analyze \
  -F "file=@video.mp4" -F "model=qwen3.5:0.8b"

# Streaming SSE
curl -X POST http://localhost:6060/api/v1/analyze/stream \
  -F "file=@video.mp4" --no-buffer
```

### SSE Event Format

```
event: init
data: {"total_frames": 12, "video_fps": 30.0, "duration_seconds": 12.4}

event: frame
data: {"index": 0, "caption": "...", "timestamp_seconds": 0.0}

event: frame
data: {"index": 1, "caption": "...", "timestamp_seconds": 1.0}

event: summary
data: {"caption": "..."}

event: done
data: {"frame_count": 12, "duration_seconds": 12.4, "device_used": "mps", "model_id": "qwen3.5:0.8b"}
```

The `init` event is emitted before inference begins — use it to show accurate totals and trigger UI setup.

---

## Architecture

```
insightcap/
├── config.py               SamplerConfig, InferenceConfig
├── device.py               detect_device() → mps/cuda/cpu
├── video/
│   ├── reader.py           VideoReader (OpenCV wrapper)
│   └── sampler.py          FrameSampler (interval-based)
├── prompt/
│   └── builder.py          PromptBuilder (frame → bytes + context prompt)
├── inference/
│   ├── base.py             CaptionBackend (ABC)
│   ├── ollama_backend.py   OllamaBackend
│   └── factory.py          get_backend()
├── pipeline.py             CaptionPipeline → CaptionResult (time-limited)
└── cli.py                  Click CLI entrypoint
```

### Sampling Strategy

Fully automatic — no user configuration:

- `frame_interval = round(video_fps)` → ~1 frame per second
- `max_frames = 20` → hard cap
- Pipeline stops after `duration_seconds` wall-clock time

### Temporal Context

Each frame caption prompt includes the last 3 captions for narrative continuity, producing video-level descriptions rather than isolated frame observations.

---

## Known Limitations

- Ollama must be running before starting the API (`ollama serve`)
- Sequential inference — one Ollama call per frame, no concurrency
- Sync is time-based approximation, not frame-perfect
- No authentication or rate limiting on the API
