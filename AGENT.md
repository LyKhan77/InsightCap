# AGENT.md - InsightCap Project Context

## Project Overview

### Purpose

**InsightCap** is a video understanding system for generating captions from uploaded videos and live RTSP camera streams.

### Definition

InsightCap is a Python application with three layers:

1. **Core engine**: reads frames, builds prompts, runs VLM inference, and returns captions.
2. **API**: exposes uploaded-video analysis and RTSP monitoring endpoints.
3. **Web app**: Streamlit interface for video mode and RTSP mode.

---

## Key Features

- Uploaded video analysis through FastAPI and Streamlit.
- SSE streaming for uploaded-video captions: `init`, `frame`, `summary`, `done`.
- RTSP live monitoring with session lifecycle API.
- RTSP live preview through MJPEG endpoint.
- RTSP live events through WebSocket endpoint.
- Frame sampling and temporal context prompts.
- Summary generation from frame captions.
- vLLM OpenAI-compatible inference backend as current default.
- CLI entrypoint for local video analysis.
- Unit tests for vLLM backend behavior.

---

## Architecture

```
web/ Streamlit UI
  ├─ video mode: upload local video, stream captions over SSE
  └─ rtsp mode: start camera session, show MJPEG preview + WebSocket captions

api/ FastAPI
  ├─ /api/v1/analyze: uploaded-video JSON result
  ├─ /api/v1/analyze/stream: uploaded-video SSE result
  ├─ /api/v1/rtsp/sessions: RTSP session create/list/get/delete
  ├─ /api/v1/rtsp/sessions/{id}/preview.jpg
  ├─ /api/v1/rtsp/sessions/{id}/preview.mjpeg
  └─ /api/v1/rtsp/sessions/{id}/events: WebSocket events

insightcap/ core engine
  ├─ VideoReader / LiveStreamReader: OpenCV file and RTSP reads
  ├─ FrameSampler: sampled frames from uploaded videos
  ├─ PromptBuilder: frame, live frame, and summary prompts
  ├─ CaptionPipeline: uploaded-video orchestration
  └─ CaptionBackend: vLLM
```

---

## Project Structure

```
InsightCap/
├── api/                              # FastAPI layer
│   ├── main.py                       # App setup, CORS, routers, health, RTSP shutdown hook
│   ├── service.py                    # Async bridge to CaptionPipeline for uploaded videos
│   ├── schemas.py                    # Uploaded-video Pydantic schemas
│   ├── rtsp_service.py               # RTSP session workers, reconnect, preview, caption events
│   ├── rtsp_schemas.py               # RTSP request/response/event schemas
│   └── routes/
│       ├── analyze.py                # /api/v1/analyze and /api/v1/analyze/stream
│       └── rtsp.py                   # RTSP sessions, preview.jpg, preview.mjpeg, WebSocket events
│
├── insightcap/                       # Core captioning engine
│   ├── pipeline.py                   # Uploaded-video orchestration and summary generation
│   ├── config.py                     # Sampler and inference config; default backend: vllm
│   ├── device.py                     # MPS/CUDA/CPU detection
│   ├── cli.py                        # Local CLI entrypoint
│   ├── video/
│   │   ├── reader.py                 # OpenCV local video reader
│   │   ├── live_reader.py            # OpenCV RTSP/live stream reader
│   │   └── sampler.py                # Frame sampling for uploaded videos
│   ├── inference/
│   │   ├── base.py                   # CaptionBackend interface
│   │   ├── factory.py                # Backend selector: vllm
│   │   ├── vllm_backend.py           # OpenAI-compatible vLLM backend
│   └── prompt/
│       └── builder.py                # Frame, live frame, and summary prompt builder
│
├── web/                              # Streamlit interface
│   ├── app.py                        # Mode selector, video mode, RTSP mode, layout, styling
│   ├── components/
│   │   ├── sidebar.py                # Video upload controls and RTSP session controls
│   │   ├── streaming_panel.py        # Uploaded-video stream/status panel
│   │   ├── results_panel.py          # Uploaded-video captions, summary, export UI
│   │   └── rtsp_panel.py             # RTSP MJPEG preview and WebSocket captions panel
│   ├── utils/
│   │   ├── api_client.py             # FastAPI HTTP client
│   │   ├── state_manager.py          # Streamlit session-state helpers
│   │   └── prompts.py                # Prompt presets/helpers
│   └── .streamlit/
│       └── config.toml               # Streamlit theme config
│
├── tests/
│   └── test_vllm_backend.py          # Unit tests for vLLM backend and backend factory
│
├── test/                             # Local notes/log artifacts
├── docker-compose.yml                # Local vLLM OpenAI server on port 8060
├── requirements.txt                  # Python dependencies
├── README.md                         # User-facing project documentation
├── API.md                            # API documentation
├── ARCHITECTURE.md                   # Architecture documentation
└── AGENT.md                          # Agent working context and rules
```

---

## Current State - ALWAYS UPDATE this Section based on Changes

### Being Developed

- vLLM-first inference service development.
- RTSP live monitoring flow in API and Streamlit.
- Browser-side RTSP live captions through WebSocket.
- MJPEG preview bridge for RTSP stream display.

### Current Problems

- RTSP processing uses one worker thread/session and synchronous frame inference; concurrency is limited.
- API has no authentication, authorization, or rate limiting.
- Uploaded-video and RTSP inference depend on a running local vLLM OpenAI-compatible server.
- vLLM runtime smoke test is pending: `docker compose up -d vllm` starts downloading the image, but the official image has multi-GB layers and was stopped before completion.
- Uploaded-video SSE sync is duration-based, not frame-perfect.
- Several docs and source files are modified in the working tree; keep this section updated after every meaningful code change.

### Checkpoint

- Default `InferenceConfig.backend` is `vllm`.
- Default `InferenceConfig.vllm_base_url` is `http://localhost:8060/v1`.
- `VLLMBackend` exists and is covered by `tests/test_vllm_backend.py`.
- `docker-compose.yml` serves vLLM on host/container port `8060`.
- `web/app.py` header now displays `VLLM_BACKEND`.
- FastAPI includes analyze and RTSP routers.
- RTSP session service supports create/list/get/delete, reconnect, preview JPEG/MJPEG, and WebSocket events.
- Streamlit includes a mode selector with video mode and RTSP mode.
- `AGENT.md`, `README.md`, `API.md`, `ARCHITECTURE.md`, API files, inference files, web sidebar, requirements, tests, and docker compose currently show local git changes.

---

## Contact & Resources

- **Current Backend**: vLLM OpenAI-compatible server
- **Served Model Name**: `qwen3.5:0.8b`
- **Model Source**: `Qwen/Qwen3.5-0.8B`
- **vLLM Base URL**: `http://localhost:8060/v1`
- **vLLM Docker Service**: `insightcap-vllm`
- **API Port**: `6060`
- **Web Port**: `8501`
- **Main API Docs**: `API.md`
- **Architecture Docs**: `ARCHITECTURE.md`
- **Project Docs**: `README.md`

===========================

# RULES - DO NOT CHANGE or EDIT this Section

## Important Notes - Project RULES

- Always use relevant skills to help with tasks.
- Always ask the user if there are any plans or discussions that need to be validated.
- Always provide a summary after finishing a task.
- Always update `README.md` whenever there are changes to key features and the app's workflow. Please note the section commands that must not be changed.
- Commit every function change so you can roll back and view the code history in case of a malfunction or a failed change.
- Do not re-read files that have already been read in this session unless necessary.
- Minimize non-essential tool calls.
- Save every plan or specification to the `docs/plans/` folder so you can track which plans have been created or are currently being created. This allows you to resume the session if the AI agent's token expires. USE `Superpowers` skill to provide the plan.

===========================

# AGENTS.md — DO NOT EDIT BELOW

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
