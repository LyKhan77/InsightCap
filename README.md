# InsightCap

Video understanding and captioning system powered by `Qwen/Qwen3.5-0.8B` via vLLM.

Analyzes a video file, generates per-frame captions with temporal context, and produces a coherent narrative summary — all streamed in real-time to the browser.

The API supports two separate modes:

- **Video Input Mode**: upload a finite video file and receive frame captions plus a final summary
- **RTSP Camera Mode**: start a live RTSP monitoring session through a separate API namespace

## Documentation

- [API Documentation](API.md)
- [System Architecture](ARCHITECTURE.md)

## Prerequisites

1. **Docker + NVIDIA Container Toolkit** installed and able to run GPU containers.

2. vLLM is provided by `docker-compose.yml` as an OpenAI-compatible server.
   The first run pulls a large `vllm/vllm-openai` image, so expect the first
   startup to take time.

   The service loads `Qwen/Qwen3.5-0.8B` and serves it under the alias
   `qwen3.5:0.8b` at `http://localhost:8060/v1`.

3. By default the container uses GPU `2` (`NVIDIA GeForce RTX 4090`). Override
   with `VLLM_GPU_DEVICE=0 docker compose up vllm` if needed.

## Setup

```bash
cd /path/to/video-captioning
python3 -m venv env
source env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Running the Full System

```bash
# Terminal 1: Start vLLM service
docker compose up vllm

# Wait until this succeeds:
curl http://localhost:8060/health

# Terminal 2: Start API server
source env/bin/activate
uvicorn api.main:app --reload --port 6060

# Confirm API sees vLLM:
curl http://localhost:6060/health

# Terminal 3: Start Streamlit Web App (legacy)
source env/bin/activate
cd web && streamlit run app.py
```

Access the legacy Streamlit app at **http://localhost:8501**

### Production Frontend Prototype

The redesigned frontend lives in `frontend/`. This is currently a Next.js +
TypeScript dummy prototype for validating the production UI before backend
integration. It does not call FastAPI, SSE, WebSocket, or MJPEG endpoints yet.

```bash
cd frontend
npm install
npm run dev
```

Access the production frontend prototype at **http://localhost:3000**

For background mode after the vLLM image is fully downloaded:

```bash
# Terminal 1: keep vLLM in the background
docker compose up -d vllm

# Terminal 2: API
source env/bin/activate
uvicorn api.main:app --reload --port 6060

# Terminal 3: Streamlit Web (legacy)
source env/bin/activate
cd web && streamlit run app.py
```

---

## Web Interface

The production frontend prototype in `frontend/` is the new target UI. It uses
a white, product-focused design system from `DESIGN.md` and mirrors the
Streamlit workflows with local dummy state:

- **Select Mode Page**: choose `Video Analysis` or `RTSP Monitoring`
- **Left control rail**: upload/source configuration, model, prompt presets, and custom prompts
- **Main workspace**: preview panel, live captions panel, summary/export, and metadata strip

The existing `web/` Streamlit interface is retained as a legacy app during the
transition:

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

## Frontend Checks

```bash
cd frontend
npm run lint
npm run build
npm run test:e2e
```

If Playwright browsers are not installed on the remote machine yet, run
`npx playwright install chromium` once from `frontend/`.

## Known Limitations

- vLLM must be running before analysis requests are sent (`docker compose up vllm`)
- Sequential inference — one vLLM chat-completion call per frame, no frame batching yet
- Sync is time-based approximation, not frame-perfect
- The production frontend is currently dummy/local-state only; backend integration is a later phase
- The Streamlit web app remains available as legacy during transition
- No authentication or rate limiting on the API
