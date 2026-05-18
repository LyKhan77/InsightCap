# InsightCap

Video understanding and captioning system powered by `Qwen/Qwen3.5-2B` via vLLM.

Analyzes a video file, generates 10-sampled-frame segment captions with temporal context, and produces a coherent narrative summary — all streamed in real-time to the browser.

The API supports two separate modes:

- **Video Input Mode**: upload a finite video file and receive segment captions plus a final summary
- **RTSP Camera Mode**: start a live RTSP monitoring session that captions 10 sampled-frame segments through a separate API namespace
- **Auto-Labelling**: optional YOLOE pseudo-labelling that exports raw frames, overlays, JSONL metadata, and YOLO labels from 10-frame chunks

## Documentation

- [API Documentation](API.md)
- [System Architecture](ARCHITECTURE.md)

## Prerequisites

1. **Docker + NVIDIA Container Toolkit** installed and able to run GPU containers.

2. vLLM is provided by `docker-compose.yml` as an OpenAI-compatible server.
   The first run pulls a large `vllm/vllm-openai` image, so expect the first
   startup to take time.

   The service loads `Qwen/Qwen3.5-2B` and serves it under the alias
   `qwen3.5:2b` at `http://localhost:8060/v1`.

3. By default the container uses GPU `2` (`NVIDIA GeForce RTX 4090`). Override
   with `VLLM_GPU_DEVICE=0 docker compose up vllm` if needed.

4. Auto-Labelling uses Ultralytics on the API process. Set `AUTO_LABEL_GPU_DEVICE=0` to keep YOLOE on GPU 0 while vLLM stays on GPU 2.

## Setup

```bash
cd /path/to/video-captioning
python3 -m venv env
source env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Running the Full System

Simple LAN/dev startup:

```bash
./scripts/dev-lan.sh
```

Then open the printed frontend URL, for example `http://192.168.x.x:3060`.

Manual startup:

```bash
# Terminal 1: Start vLLM service
docker compose up vllm

# Wait until this succeeds:
curl http://localhost:8060/health

# Terminal 2: Start API server
source env/bin/activate
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 6060

# Confirm API sees vLLM:
curl http://localhost:6060/health

# Terminal 3: Start Next.js frontend
cd frontend
npm install
npm run dev -- --hostname 0.0.0.0
```

Access the production frontend at **http://localhost:3060**.

For background mode after the vLLM image is fully downloaded:

```bash
# Terminal 1: keep vLLM in the background
docker compose up -d vllm

# Terminal 2: API
source env/bin/activate
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 6060

# Terminal 3: Frontend
cd frontend && npm run dev -- --hostname 0.0.0.0
```

---

## Web Interface

The production frontend in `frontend/` is the primary web interface. It uses a
white, product-focused design system from `DESIGN.md` with multi-page routing
and direct FastAPI integration:

- **Mode Switch Page** (`/`): choose `Video` or `RTSP` monitoring mode
- **Video Mode** (`/video`): upload analysis streamed from FastAPI SSE
- **RTSP Mode** (`/rtsp`): MJPEG preview plus RTSP caption events over WebSocket
- **Floating controls drawer**: settings accessible via gear icon in header
- **Light/dark theme**: persisted via localStorage

### Video Mode

**How it works:**
1. Upload a video in the sidebar
2. Select model (default: `qwen3.5:2b`)
3. Click `[ INITIATE_ANALYSIS ]`
4. Frontend posts to `/api/v1/analyze/stream`
5. Backend emits `init`, one `frame` event per 10 sampled-frame segment, `summary`, and `done` SSE events
6. Video auto-plays; captions reveal progressively as video reaches each segment's time range
7. Pipeline state shows phase: uploading → analyzing (X/Y revealed) → summarizing → complete
8. Final summary and export button appear after all captions are revealed
9. Video controls re-enabled once backend finishes, allowing seek while captions continue revealing
10. Optional Auto-Labelling can be enabled in the drawer before analysis; it labels each sampled chunk until the configured duration ends or the video job finishes

No FPS or frame interval config needed — sampling is auto-computed from the video.

### RTSP Mode

1. Choose `RTSP` on the mode selection page
2. Enter the RTSP URL and optional session name in the sidebar
3. Click `[ START_MONITORING ]`
4. The left panel shows a live MJPEG preview bridge of the RTSP camera
5. The right panel subscribes to RTSP live events over WebSocket and appends one caption per 10 sampled-frame segment
6. Optional Auto-Labelling can be enabled in the drawer; it runs on completed 10-frame chunks for the configured duration
7. When the Auto-Labelling schedule ends, RTSP preview and caption monitoring continue running
8. Click `[ STOP_MONITORING ]` to end the session

### Auto-Labelling Output

Auto-Labelling uses YOLOE small by default (`yoloe-26s-seg.pt`). The label prompt is optional: when disabled or left blank, object labels are extracted from the caption for each chunk. Scheduling can run for a fixed duration or in Automatic mode until the user stops it manually (or the video job/session ends). The MVP exports bbox-only labels and treats generated boxes as pseudo-labels until human-reviewed. Generated artifacts are written under `datasets/auto-label/<mode>/<job_id>/`:

- `images/`: raw sampled frames
- `labels/`: YOLO detection labels
- `overlays/`: annotated screenshots
- `annotations.jsonl`: per-frame metadata, caption context, prompt, model, and detections
- `data.yaml`: YOLO training config

The local ONNX export (`models/yoloe/yoloe-26s-seg.onnx`) is kept for experiments, but the UI uses `.pt` models because YOLOE text prompts require `set_classes()`, which the exported ONNX wrapper does not expose.

---

## CLI

```bash
# Basic caption (summary only)
python -m backend.core.cli path/to/video.mp4

# Verbose (segment captions + summary)
python -m backend.core.cli path/to/video.mp4 --verbose

# Custom model
python -m backend.core.cli path/to/video.mp4 --model qwen3.5:2b

# Save to JSON
python -m backend.core.cli path/to/video.mp4 --output result.json
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
- Uploaded-video and RTSP analysis both batch 10 sampled frames per caption; uploaded videos also emit a final partial segment when fewer than 10 sampled frames remain
- Sync is time-based approximation, not frame-perfect
- No authentication or rate limiting on the API
- Auto-Labelling depends on `ultralytics` and may download YOLOE weights on first use
- Generated Auto-Labelling boxes are pseudo-labels and should be reviewed before use as ground truth
