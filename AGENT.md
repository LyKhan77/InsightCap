# AGENT.md - InsightCap Project Context

## Project Overview

### Purpose

**InsightCap** is a video understanding and captioning system that analyzes videos and generates textual descriptions of activities, objects, and events within video content. Built as a modular three-layer architecture: core engine → API → web interface.

### Primary Goals

1. Build an efficient pipeline for video frame extraction and vision-language model inference
2. Generate accurate narrative video captions with temporal context across frames
3. Provide a modular architecture (`Engine -> API -> Web`) for easy integration
4. Deliver real-time streaming captions synchronized with video playback

---

## Key Features

### Current Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Video Reading** | OpenCV-based video file parsing (MP4, AVI, MOV, MKV, WEBM, MPEG) | Implemented |
| **Auto Frame Sampling** | ~1 frame/sec auto-computed from video fps, max 20 frames, no user config needed | Implemented |
| **Temporal Context Captioning** | Each frame prompt includes last 3 captions for narrative continuity | Implemented |
| **Time-Limited Pipeline** | Pipeline stops after `duration_seconds` wall-clock time — syncs with video end | Implemented |
| **Summary Caption** | Aggregated narrative summary of full video content | Implemented |
| **CLI Interface** | Command-line tool for video analysis | Implemented |
| **REST API** | FastAPI endpoints for analyze and analyze/stream | Implemented |
| **SSE Streaming** | Real-time frame captions via Server-Sent Events with `init` pre-event | Implemented |
| **Web Interface** | Streamlit dual-panel UI with industrial dark theme | Implemented |
| **JSON Export** | Downloadable analysis results | Implemented |

### Planned Features

| Feature | Description | Priority |
|---------|-------------|----------|
| WebSocket Live Captioning | Real-time caption from camera/stream | High |
| Batch Processing | Queue-based multi-video analysis | Medium |
| Model Switching | Support alternative VLM models | Medium |
| Docker Deployment | Containerized production deployment | High |

---

## Architecture

### Layer Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        LAYER 3: WEB APP                         │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Streamlit Interface (web/)                                 │ │
│  │  - Video upload & autoplay-locked preview                   │ │
│  │  - LIVE_STREAM panel (left): video + status                 │ │
│  │  - LIVE_CAPTIONS panel (right): real-time streaming text    │ │
│  │  - Final summary + JSON export                              │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        LAYER 2: API                             │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  FastAPI Server (api/)                                      │ │
│  │  - POST /api/v1/analyze      → Full JSON response          │ │
│  │  - POST /api/v1/analyze/stream → SSE streaming            │ │
│  │  - GET  /health               → Health check              │ │
│  │  - AnalysisService (async bridge)                           │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LAYER 1: CORE ENGINE                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Pipeline (insightcap/)                                     │ │
│  │  ├── video/                                                 │ │
│  │  │   ├── reader.py      → OpenCV video reading             │ │
│  │  │   └── sampler.py     → Frame extraction logic           │ │
│  │  ├── inference/                                             │ │
│  │  │   ├── base.py        → CaptionBackend ABC                │ │
│  │  │   ├── ollama_backend.py → Ollama integration            │ │
│  │  │   └── factory.py     → Backend instantiation            │ │
│  │  ├── prompt/                                                │ │
│  │  │   └── builder.py     → Prompt construction + context    │ │
│  │  ├── pipeline.py        → CaptionPipeline orchestration     │ │
│  │  ├── config.py          → Configuration dataclasses          │ │
│  │  ├── device.py          → Device detection (mps/cuda/cpu)   │ │
│  │  └── cli.py             → Command-line interface             │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### SSE Event Flow (`/analyze/stream`)

```
1. init    → {total_frames, video_fps, duration_seconds}   ← sent before pipeline starts
2. frame   → {index, caption, timestamp_seconds}           ← one per processed frame
3. summary → {caption}                                     ← aggregated narrative
4. done    → {frame_count, duration_seconds, device_used, model_id, video_fps, frame_interval}
```

The `init` event is emitted immediately after reading video metadata, before any inference begins. The frontend uses this to display the correct total and trigger video autoplay.

### Auto-Sampling Strategy

Frame sampling is fully automatic — no user configuration required:

```python
frame_interval = max(1, round(video_fps))   # ~1 frame per second
max_frames     = 20                          # hard cap

# Pipeline stops early if wall-clock time exceeds video duration:
deadline = time.monotonic() + duration_seconds
```

For a 30fps video: `frame_interval=30` → captures frames at 0s, 1s, 2s, ...

### Temporal Context in Prompts

Each frame is captioned with the last 3 captions as context:

```
Previous frame descriptions:
Frame 1: ...
Frame 2: ...
Frame 3: ...

Now describe frame 4 of 8, continuing the narrative. [frame_prompt]
```

This produces coherent video-level narrative rather than isolated frame descriptions.

### Directory Structure

```
video-captioning/
├── api/                          # Layer 2: FastAPI endpoints
│   ├── main.py                   # App initialization & CORS
│   ├── routes/
│   │   └── analyze.py            # /analyze endpoints
│   ├── service.py                # Async bridge to pipeline
│   └── schemas.py                # Pydantic request/response models
│
├── insightcap/                   # Layer 1: Core engine
│   ├── video/
│   │   ├── reader.py             # OpenCV video reading
│   │   └── sampler.py            # Frame extraction
│   ├── inference/
│   │   ├── base.py               # CaptionBackend abstract class
│   │   ├── ollama_backend.py     # Ollama implementation
│   │   └── factory.py            # Backend factory
│   ├── prompt/
│   │   └── builder.py            # Prompt construction with temporal context
│   ├── pipeline.py               # Main orchestration + time limit
│   ├── config.py                 # Config dataclasses
│   ├── device.py                 # Device detection
│   └── cli.py                    # CLI entrypoint
│
├── web/                          # Layer 3: Streamlit interface
│   ├── app.py                    # Main Streamlit app
│   ├── components/
│   │   ├── sidebar.py            # Upload & model selection
│   │   ├── streaming_panel.py    # Video player + status
│   │   └── results_panel.py      # Live captions + final summary
│   ├── utils/
│   │   ├── api_client.py         # HTTP client for API
│   │   └── state_manager.py      # Session state management
│   └── .streamlit/
│       └── config.toml           # Theme configuration
│
├── PRD.md                        # Product Requirements Document
├── README.md                     # Project documentation
└── AGENT.md                      # This file
```

---

## Current Development Status

### Completed Phases

#### Phase 1: Core Engine ✅
- Video reading via OpenCV
- Frame sampling (interval-based, auto-computed)
- Ollama backend integration with Qwen3.5:0.8B
- Temporal context prompt engineering
- Time-limited pipeline (stops at video duration)
- CLI interface
- Device detection (MPS/CUDA/CPU fallback)

#### Phase 2: API Layer ✅
- FastAPI server on port 6060
- POST /api/v1/analyze — Full JSON response
- POST /api/v1/analyze/stream — SSE streaming with `init` pre-event
- GET /health — Health check endpoint
- Multipart file upload support
- Async service bridge with auto-sampling

#### Phase 3: Web App ✅
- Industrial dark theme Streamlit interface (JetBrains Mono + Space Grotesk)
- Dual-panel layout: LIVE_STREAM (left) + LIVE_CAPTIONS (right)
- Real-time streaming captions via `st.empty()` placeholder pattern
- Video autoplay + controls locked during analysis
- Initialization phase before video starts (pre-computes frame count)
- JSON export functionality
- Metadata display (frames, duration, device, model)

### Known Limitations

1. **Sequential Processing**: Single Ollama call per frame (no concurrency)
2. **Sync Approximation**: Video and captions end together via time limit, not frame-perfect sync
3. **Memory Pressure**: Concurrent uploads may cause memory issues
4. **No Authentication**: API is open without auth/rate limiting
5. **Ollama Dependency**: Requires Ollama server running locally

### Dependencies

```
# Core
opencv-python>=4.8.0
ollama>=0.4.0
Pillow>=10.0.0
click>=8.1.0
numpy>=1.24.0
torch>=2.2.0

# API
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
python-multipart>=0.0.9

# Web
streamlit>=1.28.0
requests>=2.31.0
```

### Running the Application

```bash
# Prerequisite: Start Ollama server
ollama serve
ollama pull qwen3.5:0.8b

# Terminal 1: Start API (Layer 2)
uvicorn api.main:app --reload --port 6060

# Terminal 2: Start Web App (Layer 3)
cd web && streamlit run app.py

# Terminal 3: CLI Usage (Layer 1)
python -m insightcap.cli video.mp4 --verbose
```

### Test Commands

```bash
# Health check
curl http://localhost:6060/health

# Analyze video (auto-sampling, no fps/frames config needed)
curl -X POST http://localhost:6060/api/v1/analyze \
  -F "file=@video.mp4" -F "model=qwen3.5:0.8b"

# Streaming SSE
curl -X POST http://localhost:6060/api/v1/analyze/stream \
  -F "file=@video.mp4" --no-buffer
```

---

## Development Guidelines

### Code Conventions

1. **Language**: English for code, docs, API contracts
2. **Type Hints**: Use Python type hints throughout
3. **Docstrings**: Google-style docstrings for classes/functions
4. **Imports**: Use `from __future__ import annotations` for forward refs
5. **Error Handling**: Raise specific exceptions with descriptive messages

### Architecture Principles

1. **Separation of Concerns**: Each layer handles its domain
2. **Async Bridge**: API layer uses `asyncio.to_thread` for sync engine
3. **Streaming First**: Prefer SSE/streaming for real-time updates
4. **Config Injection**: Pass configs as parameters, not globals
5. **Auto-compute over user config**: Sampling params derived from video metadata

### Device Strategy

```python
# Priority: MPS (Apple Silicon) > CUDA (NVIDIA) > CPU
device = detect_device()  # Returns: 'mps', 'cuda', or 'cpu'
```

### Real-Time Streaming Pattern (Streamlit)

```python
# st.empty() placeholder updated per-frame — no st.rerun() mid-stream
with col_right:
    with st.container(border=True):
        captions_placeholder = st.empty()

for event in api_client.analyze_stream(...):
    if "total_frames" in event:          # init: start video
        render_stream_analyzing_start()
    elif "index" in event:               # frame: update captions
        with captions_placeholder.container():
            render_live_captions_streaming(frame_captions)
```

---

## Future Roadmap

### Phase 4: Production Hardening (Planned)
- Docker containerization
- Queue-based processing
- Model hot-swapping
- Performance monitoring

### Phase 5: Advanced Features (Planned)
- WebSocket live captioning from camera
- Batch video processing
- User authentication
- PostgreSQL result storage

---

## Contact & Resources

- **Model**: Qwen3.5:0.8B via Ollama
- **API Port**: 6060
- **Web Port**: 8501
- **Development Machine**: Apple Silicon M4
- **PRD Reference**: PRD.md
