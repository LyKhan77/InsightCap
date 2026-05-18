# AGENT.md - InsightCap Project Context

## Project Overview

### Purpose

**InsightCap** is a video understanding system for generating captions from uploaded videos and live RTSP camera streams.

### Definition

InsightCap is a Python + Next.js application with three layers:

1. **Core engine**: reads frames, builds prompts, runs VLM inference, and returns captions.
2. **API**: exposes uploaded-video analysis and RTSP monitoring endpoints.
3. **Web app**: Next.js production frontend for video mode and RTSP mode.

---

## Key Features

- Uploaded video analysis through FastAPI and the Next.js frontend.
- SSE streaming for uploaded-video captions: `init`, `frame`, `summary`, `done`, plus Auto-Labelling status events when enabled.
- RTSP live monitoring with session lifecycle API.
- RTSP live preview through MJPEG endpoint.
- RTSP live events through WebSocket endpoint, with one caption per 10 sampled-frame segment.
- Autonomous Auto-Labelling for Video and RTSP modes from completed 10-frame chunks.
- YOLOE-based object pseudo-labelling exports raw frames, overlays, JSONL metadata, YOLO bbox labels, and `data.yaml`.
- Frame sampling and temporal context prompts.
- Summary generation from frame captions.
- vLLM OpenAI-compatible inference backend as current default.
- CLI entrypoint for local video analysis.
- Unit tests for vLLM backend, segment pipeline, video analysis, RTSP service, and Auto-Labelling behavior.

---

## Architecture

```
frontend/ Next.js production UI
  ├─ / mode switch: choose Video or RTSP
  ├─ /video: upload analysis, live stream + captions panels
  └─ /rtsp: live monitoring, MJPEG preview + captions panels

backend/app/ FastAPI
  ├─ /api/v1/analyze: uploaded-video JSON result
  ├─ /api/v1/analyze/stream: uploaded-video SSE result
  ├─ /api/v1/auto-label/overlay: generated overlay preview
  ├─ /api/v1/rtsp/sessions: RTSP session create/list/get/delete
  ├─ /api/v1/rtsp/sessions/{id}/auto-label/start|stop
  ├─ /api/v1/rtsp/sessions/{id}/preview.jpg
  ├─ /api/v1/rtsp/sessions/{id}/preview.mjpeg
  └─ /api/v1/rtsp/sessions/{id}/events: WebSocket events

backend/core/ core engine
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
├── frontend/                        # Next.js production UI
│   ├── src/app/
│   │   ├── page.tsx                 # / — Mode Switch Page (hero + cards)
│   │   ├── video/page.tsx           # /video — Video Mode page
│   │   ├── rtsp/page.tsx            # /rtsp — RTSP Mode page
│   │   ├── layout.tsx               # Root layout (fonts, metadata)
│   │   └── globals.css              # CSS variables (light/dark themes)
│   ├── src/components/
│   │   ├── ModeSwitchPage.tsx       # Hero + Video/RTSP option cards
│   │   ├── PageHeader.tsx           # Shared header (logo, mode label, theme, drawer trigger)
│   │   ├── ControlDrawer.tsx        # Slide-in drawer from right + floating trigger
│   │   ├── VideoControls.tsx        # Video controls content (for drawer)
│   │   ├── VideoModePage.tsx        # Video page orchestrator
│   │   ├── VideoWorkspace.tsx       # Video live stream + captions panels
│   │   ├── RtspControls.tsx         # RTSP controls content (for drawer)
│   │   ├── RtspModePage.tsx         # RTSP page orchestrator
│   │   ├── RtspWorkspace.tsx        # RTSP live stream + captions panels
│   │   ├── CaptionsPanel.tsx        # Live captions display (shared)
│   │   ├── MetadataStrip.tsx        # Metadata bar (shared)
│   │   ├── AutoLabelControls.tsx    # Auto-Labelling controls for Video/RTSP drawers
│   │   ├── AutoLabelPanel.tsx       # Auto-Labelling status, latest overlay, dataset path
│   │   ├── Button.tsx               # Button component variants
│   │   ├── StatusBadge.tsx          # Status indicator badges
│   │   └── PromptEditor.tsx         # Prompt textarea editor
│   ├── src/lib/
│   │   ├── types.ts                 # TypeScript types
│   │   ├── use-theme.ts             # Theme hook (localStorage)
│   │   ├── api.ts                   # FastAPI client helpers
│   │   ├── auto-label.ts            # Auto-Labelling defaults/payload/status helpers
│   │   ├── video-stream.ts          # Uploaded-video SSE parser
│   │   ├── rtsp-events.ts           # RTSP WebSocket event normalizer
│   │   └── export.ts                # JSON export utility
│   ├── src/data/
│   │   └── prompts.ts               # Video and RTSP prompt presets
│   ├── tests/
│   │   └── insightcap.spec.ts       # Playwright e2e tests
│   ├── tailwind.config.ts           # Tailwind + design tokens
│   └── package.json                 # Webpack dev server on port 3060
│
├── backend/                          # FastAPI + core backend package
│   ├── app/
│   │   ├── main.py                   # App setup, CORS, routers, health, RTSP shutdown hook
│   │   ├── api/v1/routes/            # System, analyze, and RTSP routes
│   │   ├── schemas/                  # Video, RTSP Pydantic schemas
│   │   └── services/                 # Video analysis and RTSP session services
│   └── core/
│       ├── pipeline.py               # Uploaded-video orchestration and summary generation
│       ├── config.py                 # Sampler and inference config; default backend: vllm
│       ├── device.py                 # MPS/CUDA/CPU detection
│       ├── cli.py                    # Local CLI entrypoint
│       ├── video/                    # OpenCV file and RTSP readers, sampler
│       ├── inference/                # CaptionBackend and vLLM backend
│       └── prompt/                   # PromptBuilder
│
├── tests/
│   ├── test_vllm_backend.py          # Unit tests for vLLM backend and backend factory
│   ├── test_auto_label_service.py    # Auto-Labelling detector/export/scheduler tests
│   ├── test_video_analysis_service.py # Video SSE and Auto-Labelling integration tests
│   └── test_rtsp_service.py          # RTSP session and Auto-Labelling scheduler tests
│
├── test/                             # Local notes/log artifacts
├── docker-compose.yml                # Local vLLM OpenAI server on port 8060
├── requirements.txt                  # Python dependencies
├── README.md                         # User-facing project documentation
├── API.md                            # API documentation
├── ARCHITECTURE.md                   # Architecture documentation
└── AGENT.md                          # Agent working context and rules
```

===

## Current State - ALWAYS UPDATE this Section based on Changes

### Being Developed

- vLLM-first captioning pipeline is now centered on `Qwen/Qwen3.5-2B` served as `qwen3.5:2b`.
- Autonomous Auto-Labelling MVP is integrated for both Video Mode and RTSP Mode.
- Auto-Labelling currently focuses on object pseudo-label export, not activity classification.
- YOLOE is the default grounding detector for Auto-Labelling (`yoloe-26s-seg.pt`), with `yoloe-26n-seg.pt` as the lightweight option.
- The frontend remains a production-style Next.js multi-page UI with Control Drawer configuration and workspace status panels.

### Current Problems

- RTSP processing still uses one worker thread/session and synchronous segment inference; concurrency is limited.
- API still has no authentication, authorization, or rate limiting.
- Uploaded-video and RTSP inference still depend on a running local vLLM OpenAI-compatible server.
- vLLM runtime smoke test for the current `Qwen/Qwen3.5-2B` compose setup is still pending in this workspace; tests mock or unit-test the integration, but do not prove the full Docker model download/runtime path.
- Uploaded-video SSE sync is still duration-based, not frame-perfect.
- Frontend dev server still uses Webpack via `next dev --port 3060 --webpack` because Turbopack previously hit the system `fs.inotify.max_user_watches` limit.
- Auto-Labelling output is pseudo-label data only; human review is still required before treating exported boxes as ground truth.
- Auto-Labelling uses Ultralytics YOLOE in the API process and may download detector weights on first use.

### Checkpoint

- **Frontend** (`frontend/`): multi-page Next.js app with 3 routes.
  - `/` — Mode Switch Page: hero + two cards (Video / RTSP).
  - `/video` — Video Mode: full-width raw video preview + Live Captions panels, controls in floating drawer.
  - `/rtsp` — RTSP Mode: raw MJPEG preview + Live Captions panels, controls in floating drawer.
  - No bbox overlay is drawn on the live/video preview; Auto-Labelling overlay is shown only in the compact Auto-Labelling panel.
  - No mode switch in header; "Change Mode" button navigates to `/`.
  - Floating settings drawer (gear icon) slides in from right with controls.
  - Light/dark theme persisted via localStorage (`useTheme` hook).
  - DESIGN.md emerald green style (`#3ecf8e` primary, Inter font, white/near-black canvas).
  - Dev server: Webpack (`--webpack` flag), port 3060.
  - Calls FastAPI directly via `NEXT_PUBLIC_API_BASE_URL`.
  - `/video` streams uploaded-video captions over SSE and can enqueue 10-frame chunks for Auto-Labelling.
  - `/rtsp` creates backend sessions, renders MJPEG preview, subscribes to WebSocket segment caption events, and can start/stop Auto-Labelling independently from monitoring.
  - Auto-Labelling controls are available in both `VideoControls` and `RtspControls`.
  - Workspace metadata includes Auto-Labelling status, remaining time, labelled frame count, dropped frame count, latest overlay, and dataset path.
  - Playwright e2e tests mock backend SSE/REST/WS flows.
- Default `InferenceConfig.backend` is `vllm`.
- Default `InferenceConfig.model_id` is `qwen3.5:2b`.
- Default `InferenceConfig.vllm_base_url` is `http://localhost:8060/v1`.
- `docker-compose.yml` serves `Qwen/Qwen3.5-2B` as `qwen3.5:2b` on host/container port `8060`, defaults vLLM to GPU `2`, and allows 10 images per multimodal prompt.
- Auto-Labelling defaults to YOLOE small (`yoloe-26s-seg.pt`) and uses `AUTO_LABEL_GPU_DEVICE` with default GPU `0` for detector inference.
- Auto-Labelling dataset output is `datasets/auto-label/<mode>/<job_id>/` with raw images, bbox YOLO labels, overlays, JSONL metadata, and `data.yaml`.
- `VLLMBackend` supports single-frame and multi-frame image requests and is covered by `tests/test_vllm_backend.py`.
- `AutoLabelJob` exports bbox-only YOLO labels; mask/SAM export, ROI, tracking, candidate activity, and activity classifier are deferred.
- FastAPI entrypoint is `backend.app.main:app`.
- FastAPI includes system, analyze, Auto-Labelling overlay, and RTSP routers.
- RTSP session service supports create/list/get/delete, reconnect, preview JPEG/MJPEG, WebSocket segment caption events, and independent Auto-Labelling start/stop.

---

## Contact & Resources

- **Current Backend**: vLLM OpenAI-compatible server
- **Served Model Name**: `qwen3.5:2b`
- **Model Source**: `Qwen/Qwen3.5-2B`
- **vLLM Base URL**: `http://localhost:8060/v1`
- **vLLM Docker Service**: `insightcap-vllm`
- **Auto-Labelling Detector**: `yoloe-26s-seg.pt` by default; `yoloe-26n-seg.pt` lightweight option
- **Default GPU Split**: vLLM on GPU `2`; Auto-Labelling detector on `AUTO_LABEL_GPU_DEVICE` default GPU `0`
- **API Port**: `6060`
- **Frontend Port**: `3060`
- **Main API Docs**: `API.md`
- **Architecture Docs**: `ARCHITECTURE.md`
- **Project Docs**: `README.md`
- **Design System**: `DESIGN.md`

===========================

# RULES - DO NOT CHANGE or EDIT this Section

## Important Notes - Project RULES

- Always use relevant skills to help with tasks.
- Always ask the user if there are any plans or discussions that need to be validated.
- Always provide a summary after finishing a task.
- Always update `README.md` whenever there are changes to key features and the app's workflow. Please note the section commands that must not be changed.
- Commit every function change so you can roll back and view the code history in case of a malfunction or a failed change. Also UPDATE the `.gitignore` file whenever a new file is added that needs to be excluded before committing.
- Do not re-read files that have already been read in this session unless necessary.
- Minimize non-essential tool calls.
- Save every plan or specification to the `docs/plans/` folder so you can track which plans have been created or are currently being created. This allows you to resume the session if the AI agent's token expires. USE `Superpowers` skill to provide the plan. REMEMBER This file does not need to be updated unless requested. It is intended solely as a record of past information.

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
