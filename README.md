# InsightCap

Video understanding and captioning system powered by `qwen3.5:0.8b` via Ollama.

Analyzes a video file, generates per-frame captions with temporal context, and produces a coherent narrative summary — all streamed in real-time to the browser.

The API supports two separate modes:

- **Video Input Mode**: upload a finite video file and receive frame captions plus a final summary
- **RTSP Camera Mode**: start a live RTSP monitoring session through a separate API namespace

## Documentation

- [API Documentation](API.md)
- [System Architecture](ARCHITECTURE.md)

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

- **Select Mode Page**: choose `VIDEO` or `RTSP`
- **Left panel — LIVE_STREAM**: Video player (autoplays and locks during analysis)
- **Right panel — LIVE_CAPTIONS**: Captions stream in real-time as frames are processed

### Video Mode

**How it works:**
1. Upload a video in the sidebar
2. Select model (default: `qwen3.5:0.8b`)
3. Click `[ INITIATE_ANALYSIS ]`
4. Backend reads video metadata → frontend shows `INITIALIZING...`
5. Video autoplays + locks; captions stream in the right panel
6. Pipeline stops automatically when video duration is reached
7. Final narrative summary appears; video controls restored

No FPS or frame interval config needed — sampling is auto-computed from the video.

### RTSP Mode

1. Choose `RTSP` on the mode selection page
2. Enter the RTSP URL and optional session name in the sidebar
3. Click `[ START_MONITORING ]`
4. The left panel shows a live MJPEG preview bridge of the RTSP camera
5. The right panel subscribes to RTSP live events over WebSocket and appends captions as they arrive
6. Click `[ STOP_MONITORING ]` to end the session

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
- Detailed endpoint contract, examples, and troubleshooting: [API.md](API.md)

## Architecture

- System overview, layer diagram, data flow, and runtime design: [ARCHITECTURE.md](ARCHITECTURE.md)

---

## Known Limitations

- Ollama must be running before starting the API (`ollama serve`)
- Sequential inference — one Ollama call per frame, no concurrency
- Sync is time-based approximation, not frame-perfect
- The current Streamlit web app still targets uploaded video files; RTSP mode is exposed through the separate API endpoints
- No authentication or rate limiting on the API
