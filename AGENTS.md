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
- SSE streaming for uploaded-video captions: `init`, `frame`, `summary`, `done`.
- RTSP live monitoring with session lifecycle API.
- RTSP live preview through MJPEG endpoint.
- RTSP live events through WebSocket endpoint, with one caption per 10 sampled-frame segment.
- Frame sampling and temporal context prompts.
- Summary generation from frame captions.
- vLLM OpenAI-compatible inference backend as current default.
- CLI entrypoint for local video analysis.
- Unit tests for vLLM backend behavior.

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
  ├─ /api/v1/rtsp/sessions: RTSP session create/list/get/delete
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
│   │   ├── Button.tsx               # Button component variants
│   │   ├── StatusBadge.tsx          # Status indicator badges
│   │   └── PromptEditor.tsx         # Prompt textarea editor
│   ├── src/lib/
│   │   ├── types.ts                 # TypeScript types
│   │   ├── use-theme.ts             # Theme hook (localStorage)
│   │   ├── api.ts                   # FastAPI client helpers
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

===

## Current State - ALWAYS UPDATE this Section based on Changes

### Being Developed

- Frontend production UI integration in `frontend/` (Next.js multi-page architecture).
- vLLM-first inference service development.
- Backend package cleanup in `backend/`.

### Current Problems

- RTSP processing uses one worker thread/session and synchronous segment inference; concurrency is limited.
- API has no authentication, authorization, or rate limiting.
- Uploaded-video and RTSP inference depend on a running local vLLM OpenAI-compatible server.
- vLLM runtime smoke test is pending: `docker compose up -d vllm` starts downloading the image, but the official image has multi-GB layers and was stopped before completion.
- Uploaded-video SSE sync is duration-based, not frame-perfect.
- Dev server uses Webpack instead of Turbopack due to system `fs.inotify.max_user_watches` limit (65536); Turbopack crashes with FATAL panic.

### Checkpoint

- **Frontend** (`frontend/`): multi-page Next.js app with 3 routes.
  - `/` — Mode Switch Page: hero + two cards (Video / RTSP).
  - `/video` — Video Mode: full-width Live Stream + Live Captions panels, controls in floating drawer.
  - `/rtsp` — RTSP Mode: same layout, must stop monitoring before navigating back.
  - No mode switch in header; "Change Mode" button navigates to `/`.
  - Floating settings drawer (gear icon) slides in from right with controls.
  - Light/dark theme persisted via localStorage (`useTheme` hook).
  - DESIGN.md emerald green style (`#3ecf8e` primary, Inter font, white/near-black canvas).
  - Dev server: Webpack (`--webpack` flag), port 3060.
  - Calls FastAPI directly via `NEXT_PUBLIC_API_BASE_URL`.
  - `/video` streams uploaded-video captions over SSE.
  - `/rtsp` creates backend sessions, renders MJPEG preview, and subscribes to WebSocket segment caption events.
  - Playwright e2e tests mock backend SSE/REST/WS flows.
- Default `InferenceConfig.backend` is `vllm`.
- Default `InferenceConfig.vllm_base_url` is `http://localhost:8060/v1`.
- `VLLMBackend` supports single-frame and multi-frame image requests and is covered by `tests/test_vllm_backend.py`.
- `docker-compose.yml` serves vLLM on host/container port `8060` and allows 10 images per multimodal prompt.
- FastAPI entrypoint is `backend.app.main:app`.
- FastAPI includes system, analyze, and RTSP routers.
- RTSP session service supports create/list/get/delete, reconnect, preview JPEG/MJPEG, and WebSocket segment caption events.

---

## Contact & Resources

- **Current Backend**: vLLM OpenAI-compatible server
- **Served Model Name**: `qwen3.5:0.8b`
- **Model Source**: `Qwen/Qwen3.5-0.8B`
- **vLLM Base URL**: `http://localhost:8060/v1`
- **vLLM Docker Service**: `insightcap-vllm`
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
