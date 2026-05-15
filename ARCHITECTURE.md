# InsightCap - System Architecture Document

## 1. System Overview

**InsightCap** is a video understanding and captioning system that transforms video content into textual descriptions using vision-language models (VLM). The system analyzes video frames sequentially with temporal context to produce coherent narrative captions.

### 1.1 Core Value Proposition

- **Video Understanding**: Automatic extraction of activities, objects, and events from video content
- **Temporal Context**: Frame-by-frame analysis with narrative continuity across the video timeline
- **Real-time Streaming**: Live caption updates via Server-Sent Events (SSE) and WebSocket
- **Dual Mode Operation**: Static video file analysis and live RTSP camera monitoring

### 1.2 Technology Stack

| Component | Technology |
|-----------|------------|
| Core Engine | Python 3.10+ |
| VLM Backend | vLLM + Qwen/Qwen3.5-0.8B |
| Video Processing | OpenCV (cv2) |
| API Layer | FastAPI + Uvicorn |
| Web Interface | Next.js production frontend (`frontend/`) |
| Streaming | SSE (video) / WebSocket (RTSP) |
| Device Acceleration | MPS (Apple Silicon) / CUDA (NVIDIA) / CPU fallback |

---

## 2. Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LAYER 3: WEB INTERFACE                            │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Next.js Application (frontend/)                                      │  │
│  │  ├── / mode switch (Video/RTSP)                                       │  │
│  │  ├── /video upload + SSE captions                                     │  │
│  │  ├── /rtsp MJPEG preview + WebSocket captions                         │  │
│  │  ├── Floating controls drawer                                         │  │
│  │  └── JSON Export                                                      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │ HTTP/SSE/WS
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            LAYER 2: API LAYER                                │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  FastAPI Server (backend/app/)                                        │  │
│  │  ├── /api/v1/analyze          → Full JSON response                    │  │
│  │  ├── /api/v1/analyze/stream   → SSE streaming                         │  │
│  │  ├── /api/v1/rtsp/sessions    → RTSP session management               │  │
│  │  ├── /api/v1/rtsp/.../events  → WebSocket live events                 │  │
│  │  ├── /api/v1/rtsp/.../preview.mjpeg → Live preview stream            │  │
│  │  └── /health                  → Health check                          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │ Python async bridge
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LAYER 1: CORE ENGINE                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Pipeline (backend/core/)                                             │  │
│  │  ├── video/                                                           │  │
│  │  │   ├── reader.py        → VideoReader (local file OpenCV wrapper)  │  │
│  │  │   ├── sampler.py       → FrameSampler (interval extraction)       │  │
│  │  │   └── live_reader.py   → LiveStreamReader (RTSP/camera)           │  │
│  │  ├── inference/                                                        │  │
│  │  │   ├── base.py           → CaptionBackend ABC                      │  │
│  │  │   ├── vllm_backend.py    → VLLMBackend (qwen3.5:0.8b alias)       │  │
│  │  │   └── factory.py        → Backend instantiation                    │  │
│  │  ├── prompt/                                                           │  │
│  │  │   └── builder.py        → PromptBuilder (temporal context)        │  │
│  │  ├── pipeline.py           → CaptionPipeline (orchestration)          │  │
│  │  ├── config.py             → SamplerConfig, InferenceConfig           │  │
│  │  ├── device.py             → detect_device() → mps/cuda/cpu           │  │
│  │  └── cli.py                → Click CLI entrypoint                      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │ OpenAI-compatible API
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       INFERENCE RUNTIME                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  vLLM Docker Service (localhost:8060/v1)                              │  │
│  │  └── Model: Qwen/Qwen3.5-0.8B served as qwen3.5:0.8b                 │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Key Features Analysis

### 3.1 Video Input Mode

**Purpose**: Analyze uploaded video files and produce frame-by-frame captions with a final summary.

**Workflow**:
```
User Upload → Temp File → VideoReader → FrameSampler → CaptionPipeline → SSE Stream → Web UI
```

**Key Components**:

| Component | File | Responsibility |
|-----------|------|----------------|
| VideoReader | `backend/core/video/reader.py` | OpenCV wrapper for local video files |
| FrameSampler | `backend/core/video/sampler.py` | Interval-based frame extraction |
| CaptionPipeline | `backend/core/pipeline.py` | Orchestrates sampling, inference, summary |
| AnalysisService | `backend/app/services/video_analysis.py` | Async bridge to sync pipeline |

**Auto-Sampling Strategy**:
```python
frame_interval = max(1, round(video_fps))  # ~1 frame per second
max_frames = 20                             # hard cap to prevent OOM
```

**SSE Event Sequence**:
```
1. init    → {total_frames, video_fps, duration_seconds}
2. frame   → {index, caption, timestamp_seconds}  (per frame)
3. summary → {caption}
4. done    → {frame_count, duration_seconds, device_used, model_id}
```

### 3.2 RTSP Camera Mode

**Purpose**: Monitor live RTSP camera streams with real-time caption generation.

**Workflow**:
```
RTSP URL → LiveStreamReader → Background Thread → Frame Capture Loop → Inference Loop → WebSocket Events
                                      │
                                      └→ MJPEG Preview Stream → Browser
```

**Key Components**:

| Component | File | Responsibility |
|-----------|------|----------------|
| LiveStreamReader | `backend/core/video/live_reader.py` | OpenCV wrapper for RTSP streams |
| RtspSession | `backend/app/services/rtsp/` | Per-session worker thread management |
| RtspSessionService | `backend/app/services/rtsp/` | Registry and lifecycle manager |

**Session Lifecycle**:
```
POST /sessions → RtspSession.start() → Thread spawned → Connection loop
                                                │
                                                ├── capture_frames() thread
                                                └── Inference loop (sampling)
                                                        
DELETE /sessions → RtspSession.stop() → Thread.join() → Cleanup
```

**WebSocket Event Types**:
| Event | Description | Data Fields |
|-------|-------------|-------------|
| `connected` | RTSP stream connected | `source`, `width`, `height`, `fps` |
| `caption` | 10 sampled-frame segment caption generated | `seq`, `caption`, `sampled_frame_count`, `frame_seq_start`, `frame_seq_end`, `captured_at`, `processed_at`, `lag_ms` |
| `heartbeat` | Periodic status | `status`, `captions_emitted`, `reconnect_count` |
| `warning` | Recoverable error | `message`, `reconnect_count` |
| `stopped` | Session terminated | `status` |

### 3.3 Temporal Context Captioning

**Purpose**: Maintain narrative continuity by including previous captions in the prompt.

**Implementation** (`backend/core/prompt/builder.py`):

```python
def build_frame_message_with_context(
    self,
    frame,
    previous_captions: list[str],  # Last N captions
    frame_num: int,
    total_frames: int,
) -> dict:
    if previous_captions:
        context_lines = "\n".join(
            f"Frame {frame_num - len(previous_captions) + i}: {c}"
            for i, c in enumerate(previous_captions)
        )
        prompt = (
            f"Previous frame descriptions:\n{context_lines}\n\n"
            f"Now describe frame {frame_num} of {total_frames}, "
            f"continuing the narrative. {self.frame_prompt}"
        )
    # ...
```

**Configuration**:
- Uploaded-video frame prompts include the last `InferenceConfig.temporal_context_frames` captions as context.
- RTSP live prompts analyze 10 sampled frames as one segment and include the previous segment caption as text context.

### 3.4 Streaming Architecture

**Video Mode (SSE)**:
```
┌─────────────┐    POST /analyze/stream    ┌─────────────┐
│   Browser   │ ───────────────────────────│   FastAPI   │
│  (Next.js) │ ◄──────────────────────────│   Server    │
│             │     text/event-stream       │             │
└─────────────┘                            │      │      │
                                           │   async     │
                                           │   to_thread  │
                                           │      │      │
                                           │      ▼      │
                                           │ ┌─────────┐ │
                                           │ │Pipeline │ │
                                           │ │(sync)   │ │
                                           │ └─────────┘ │
                                           └─────────────┘
```

**RTSP Mode (WebSocket)**:
```
┌─────────────┐   WS /sessions/{id}/events  ┌─────────────┐
│   Browser   │ ◄────────────────────────────│   FastAPI   │
│  (Next.js) │                              │   Server    │
│             │                              │      │      │
│             │   GET /sessions/{id}/preview │      │      │
│             │ ─────────────────────────────│   MJPEG    │
│             │ ◄────────────────────────────│   stream   │
└─────────────┘                              │      │      │
                                             │   Background│
                                             │   thread    │
                                             │      │      │
                                             │      ▼      │
                                             │ ┌─────────┐ │
                                             │ │RtspSess │ │
                                             │ │(worker) │ │
                                             │ └─────────┘ │
                                             └─────────────┘
```

---

## 4. Data Flow Diagrams

### 4.1 Video Analysis Flow

```
┌──────────┐     ┌──────────┐     ┌─────────────┐     ┌──────────────┐
│  Upload  │────►│  Temp    │────►│ VideoReader │────►│ FrameSampler │
│  Video   │     │  File    │     │             │     │              │
└──────────┘     └──────────┘     └─────────────┘     └──────────────┘
                                                               │
                                          ┌────────────────────┘
                                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                        CaptionPipeline                            │
│  ┌─────────────┐    ┌─────────────────┐    ┌──────────────────┐ │
│  │ for frame   │───►│ PromptBuilder    │───►│ VLLMBackend      │ │
│  │ in frames   │    │ (add context)    │    │ .generate_frame()│ │
│  └─────────────┘    └─────────────────┘    └──────────────────┘ │
│          │                                        │              │
│          ▼                                        ▼              │
│  ┌─────────────┐                          ┌──────────────────┐  │
│  │ frame_      │                          │ yield SSE event  │  │
│  │ captions[]  │                          │ to HTTP client   │  │
│  └─────────────┘                          └──────────────────┘  │
│          │                                                       │
│          ▼                                                       │
│  ┌─────────────────┐    ┌──────────────────┐                    │
│  │ VLLMBackend     │───►│ yield SSE event  │                    │
│  │ .summarize()    │    │ "summary"        │                    │
│  └─────────────────┘    └──────────────────┘                    │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 RTSP Live Monitoring Flow

```
┌─────────────────┐
│  POST /sessions │
│  {rtsp_url}     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        RtspSession                                   │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Main Thread: _run()                                             ││
│  │  ├── LiveStreamReader(url) open                                  ││
│  │  ├── spawn capture_frames() thread                               ││
│  │  ├── emit "connected" event                                      ││
│  │  └── Loop: collect 10 sampled frames → inference → caption       ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Capture Thread: _capture_frames()                                ││
│  │  └── Loop: reader.read() → update _latest_frame → JPEG preview  ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
         │
         │ subscribe()
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   WebSocket Connection                               │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Event Loop: queue.get() → websocket.send_json(event)           ││
│  │ Events: connected, caption, heartbeat, warning, stopped        ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Component Details

### 5.1 Core Engine Components

#### `backend/core/video/reader.py` - VideoReader

```python
class VideoReader:
    """Thin wrapper around cv2.VideoCapture for reading local video files."""
    
    Properties:
        - fps: float        # Frames per second
        - frame_count: int  # Total frames in video
        - width: int        # Video width in pixels
        - height: int       # Video height in pixels
        - duration_seconds: float  # Video duration
    
    Methods:
        - open() / close()  # Context manager support
        - read_frame(index)  # Seek and read specific frame
```

#### `backend/core/video/sampler.py` - FrameSampler

```python
class FrameSampler:
    """Samples frames from a VideoReader according to SamplerConfig."""
    
    Config:
        - frame_interval: int = 10  # Capture every Nth frame
        - max_frames: int = 60      # Hard limit
    
    Methods:
        - sample(reader) -> list[ndarray]  # Extract frames
```

#### `backend/core/video/live_reader.py` - LiveStreamReader

```python
class LiveStreamReader:
    """Sequential OpenCV reader for RTSP and other live stream URLs."""
    
    Properties:
        - fps: int
        - width: int
        - height: int
    
    Methods:
        - open() / close()
        - read() -> ndarray | None  # Get next frame
```

#### `backend/core/inference/base.py` - CaptionBackend (ABC)

```python
class CaptionBackend(ABC):
    """Abstract base class for caption inference backends."""
    
    @abstractmethod
    def generate_for_frame(frame: np.ndarray, prompt: str) -> Iterator[str]:
        """Stream caption tokens for a single BGR video frame."""
    
    @abstractmethod
    def summarize(frame_captions: list[str], summary_prompt: str) -> Iterator[str]:
        """Stream a summary caption given per-frame captions."""
```

#### `backend/core/inference/vllm_backend.py` - VLLMBackend

```python
class VLLMBackend(CaptionBackend):
    """Inference backend using a vLLM OpenAI-compatible server."""
```

Key features:
- Sends image frames as OpenAI vision `image_url` data URLs
- Uses `qwen3.5:0.8b` as the served model alias
- Calls `http://localhost:8060/v1/chat/completions`
- Supports streaming and non-streaming modes

#### `backend/core/pipeline.py` - CaptionPipeline

```python
class CaptionPipeline:
    """Orchestrates video reading, frame sampling, and caption generation."""
    
    __init__:
        - sampler_config: SamplerConfig
        - inference_config: InferenceConfig
        - _sampler: FrameSampler
        - _backend: CaptionBackend
        - _prompt_builder: PromptBuilder
    
    run(video_path, time_limit_seconds, callbacks):
        Returns: CaptionResult(caption, frame_captions, frame_count, ...)
        
    Callbacks:
        - on_frame_start(frame_index, total_frames)
        - on_frame_token(token)  # Streaming
        - on_frame_done(frame_index, caption)
        - on_summary_token(token)  # Streaming
```

### 5.2 API Layer Components

#### `backend/app/main.py` - FastAPI Application

```python
app = FastAPI(title="InsightCap API", version="2.0.0")

Routers:
    - /api/v1/analyze/* → analyze_router
    - /api/v1/rtsp/* → rtsp_router
    - /health → health check

Middleware:
    - CORS (allow all origins)

Lifecycle:
    - on_event("shutdown") → rtsp_session_service.shutdown()
```

#### `backend/app/services/video_analysis.py` - AnalysisService

```python
class AnalysisService:
    """Async bridge between FastAPI routes and sync CaptionPipeline."""
    
    _MAX_FRAMES = 20  # Hard cap
    
    _compute_sampling(video_fps, total_native):
        # Returns ~1 frame per second, capped at MAX_FRAMES
        return frame_interval, total_frames
    
    run(video_path, params) -> AnalysisResponse:
        # Non-streaming full analysis
    
    run_stream(video_path, params) -> AsyncIterator[str]:
        # SSE event generator with callbacks
```

#### `backend/app/services/rtsp/` - RtspSessionService

```python
class RtspSessionService:
    """Registry and lifecycle manager for RTSP sessions."""
    
    max_active_sessions: int = 2  # Concurrent session limit
    
    Methods:
        - create_session(request) -> RTSPSessionResponse
        - get_session(session_id) -> RtspSession
        - list_sessions() -> list[RTSPSessionResponse]
        - delete_session(session_id) -> RTSPSessionResponse
        - subscribe(session_id) -> (session, subscriber_id, queue)
        - unsubscribe(session_id, subscriber_id)
        - shutdown()  # Stop all sessions

class RtspSession:
    """Owns one RTSP monitoring session and its worker thread."""
    
    Constants:
        - _HEARTBEAT_SECONDS = 5.0
        - _RECONNECT_DELAY_SECONDS = 2.0
        - _PREVIEW_INTERVAL_SECONDS = 0.1
        - _PREVIEW_MAX_WIDTH = 960
    
    Methods:
        - start()  # Launch worker thread
        - stop()  # Signal and join thread
        - snapshot() -> RTSPSessionResponse
        - get_preview_jpeg() -> bytes | None
        - subscribe() -> (subscriber_id, queue)
        - unsubscribe(subscriber_id)
```

## 6. Configuration

### 6.1 SamplerConfig

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frame_interval` | int | 10 | Capture every Nth frame (auto-computed as `round(video_fps)`) |
| `max_frames` | int | 60 | Maximum frames to extract (capped at 20 in API) |

### 6.2 InferenceConfig

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_id` | str | "qwen3.5:0.8b" | vLLM served model alias |
| `stream` | bool | False | Enable token streaming |
| `backend` | str | "vllm" | Inference backend |
| `vllm_base_url` | str | "http://localhost:8060/v1" | vLLM OpenAI-compatible API |
| `max_tokens` | int | 1024 | Maximum response tokens |
| `temporal_context_frames` | int | 3 | Previous captions in prompt |
| `frame_prompt` | str | "Describe what is happening..." | Frame instruction |
| `summary_prompt` | str | "You are given a sequence..." | Summary instruction |

### 6.3 RTSP Session Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rtsp_url` | str | required | RTSP stream URL |
| `model` | str | "qwen3.5:0.8b" | VLM model |
| `sample_every_seconds` | float | 1.0 | Sampling interval |
| `session_name` | str | hostname | Human-readable name |

---

## 7. API Reference

### 7.1 Video Analysis Endpoints

#### `POST /api/v1/analyze`

Upload video and receive complete analysis as JSON.

**Request**: `multipart/form-data`
- `file`: Video file (mp4, avi, mov, mkv, webm, mpeg)
- `model`: Model name (default: "qwen3.5:0.8b")

**Response**: `AnalysisResponse`
```json
{
    "caption": "Narrative summary of the video...",
    "frame_captions": ["Frame 1 description...", "..."],
    "frame_count": 12,
    "duration_seconds": 12.4,
    "device_used": "mps",
    "model_id": "qwen3.5:0.8b"
}
```

#### `POST /api/v1/analyze/stream`

Upload video and receive real-time updates via Server-Sent Events.

**Event Types**:
- `init`: `{total_frames, video_fps, duration_seconds}`
- `frame`: `{index, caption, timestamp_seconds}`
- `summary`: `{caption}`
- `done`: `{frame_count, duration_seconds, device_used, model_id, video_fps, frame_interval}`

### 7.2 RTSP Session Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/rtsp/sessions` | Create monitoring session |
| `GET` | `/api/v1/rtsp/sessions` | List all sessions |
| `GET` | `/api/v1/rtsp/sessions/{id}` | Get session status |
| `DELETE` | `/api/v1/rtsp/sessions/{id}` | Stop session |
| `GET` | `/api/v1/rtsp/sessions/{id}/preview.jpg` | Single JPEG frame |
| `GET` | `/api/v1/rtsp/sessions/{id}/preview.mjpeg` | MJPEG stream |
| `WS` | `/api/v1/rtsp/sessions/{id}/events` | WebSocket events |

---

## 8. Security Considerations

### 8.1 Current Limitations

| Area | Status | Risk Level |
|------|--------|------------|
| Authentication | None | High |
| Rate Limiting | None | Medium |
| Input Validation | Basic file type check | Medium |
| RTSP URL Sanitization | Credentials masked in logs | Medium |
| Session Limits | 2 concurrent RTSP sessions | Low |

### 8.2 Recommendations

1. Add API authentication (API keys or JWT)
2. Implement rate limiting per client
3. Validate RTSP URLs against allowlist
4. Add request size limits
5. Encrypt RTSP credentials in storage

---

## 9. Performance Characteristics

### 9.1 Inference Latency

| Device | Typical Frame Processing | Notes |
|--------|------------------------|-------|
| MPS (Apple Silicon M4) | 0.5-2 seconds/frame | Development optimized |
| CUDA (NVIDIA GPU) | 0.2-1 second/frame | Production target |
| CPU | 5-15 seconds/frame | Fallback only |

### 9.2 Memory Usage

| Component | Approximate Usage | Notes |
|-----------|------------------|-------|
| VideoReader | Video dependent | OpenCV buffer |
| FrameSampler | ~20 frames × W×H×3 | BGR arrays in memory |
| vLLM Backend | Model-dependent | Docker service |
| RTSP Session | ~2 streams × preview | JPEG buffer |

### 9.3 Concurrency Model

```
Video Mode: Single-threaded inference per request
           Multiple requests → Sequential processing
           
RTSP Mode:  One worker thread per session
           Frame capture thread + inference thread
           Max sessions = 2 (configurable)
```

---

## 10. Deployment Architecture

### 10.1 Development Mode

```bash
# Terminal 1: vLLM Server
docker compose up vllm

# Terminal 2: API Server
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 6060

# Terminal 3: Web App
cd frontend && npm run dev -- --hostname 0.0.0.0
```

### 10.2 Production Architecture (Recommended)

```
                    ┌─────────────────┐
                    │   Load Balancer │
                    │   (nginx/traefik)│
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ API Pod 1│  │ API Pod 2│  │ API Pod N│
        │ FastAPI  │  │ FastAPI  │  │ FastAPI  │
        └────┬─────┘  └────┬─────┘  └────┬─────┘
             │             │             │
             └─────────────┼─────────────┘
                           │
              ┌────────────┼────────────┐
              ▼             ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  vLLM 1  │ │  vLLM 2  │ │  vLLM N  │
        │ (GPU)    │ │ (GPU)    │ │ (GPU)    │
        └──────────┘ └──────────┘ └──────────┘
```

---

## 11. File Tree Summary

```
video-captioning/
├── backend/                          # FastAPI + core engine
│   ├── app/
│   │   ├── main.py                   # App initialization, CORS, routers
│   │   ├── api/v1/routes/            # Analyze, RTSP, system routes
│   │   ├── schemas/                  # Pydantic request/response models
│   │   └── services/                 # Video analysis + RTSP session services
│   └── core/                         # Caption pipeline, video, inference, prompts
│
├── frontend/                         # Layer 3: Next.js production UI
│   ├── src/app/                      # /, /video, /rtsp routes
│   ├── src/components/               # Workspace, controls, captions panels
│   └── src/lib/                      # API, SSE, WS, export, theme helpers
│
├── docs/plans/                       # Implementation plans and specs
├── docker-compose.yml                # vLLM OpenAI-compatible server
├── AGENTS.md                         # Development context
├── README.md                         # Project documentation
├── requirements.txt                  # Python dependencies
└── tests/                            # Backend unit tests
```

---

## 12. Known Limitations

1. **Sequential Inference**: Single vLLM chat-completion call per frame, no frame-level batching
2. **Time-Based Sync**: Video-caption synchronization is approximate, not frame-perfect
3. **Memory Pressure**: Concurrent uploads may cause OOM on constrained hardware
4. **No Authentication**: API is open without auth/rate limiting
5. **vLLM Dependency**: Requires Docker vLLM service running
6. **RTSP Reconnection**: Basic reconnect logic, no sophisticated error recovery

---

## 13. Future Roadmap

| Phase | Feature | Priority |
|-------|---------|----------|
| 4 | Docker containerization | High |
| 4 | Queue-based processing | High |
| 4 | Model hot-swapping | Medium |
| 5 | WebSocket live webcam capture | High |
| 5 | Batch video processing | Medium |
| 5 | PostgreSQL result storage | Low |
| 5 | User authentication | High |
| 5 | Dashboard/analytics | Low |

---

**Document Version**: 1.0.0  
**Last Updated**: March 2026
