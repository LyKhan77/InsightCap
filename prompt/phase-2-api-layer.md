# Phase 2 Prompt

## Start Phase

```text
You are helping me build Phase 2 of InsightCap.

Project name: InsightCap
Phase: API Layer and Integration
Development machine: Apple Silicon M4
Project language: English

Context:
- Phase 1 already created the core engine for video loading, frame sampling, prompt assembly, and caption execution.
- This phase must wrap the engine with a clean FastAPI interface.
- The architecture target remains Engine -> API -> Web.

Your task in this phase:
- Build a FastAPI application around the existing engine.
- Add POST /analyze for local video upload analysis.
- Define request and response schemas clearly.
- Keep the engine reusable and independent from API transport logic.
- Prepare for future streaming responses and WebSocket-based live captioning.

Constraints:
- Development is on Apple Silicon M4.
- Production portability to Linux + NVIDIA must be preserved.
- Use English for all code, API models, docs, and naming.
- Avoid tightly coupling the engine to FastAPI internals.

Expected deliverables:
- FastAPI app entrypoint
- analyze endpoint
- service layer or adapter between API and engine
- error handling strategy
- clear response model
- development run instructions

Definition of done:
- I can start the API locally.
- I can upload a short video to POST /analyze.
- The engine is called successfully from the API layer.
- Failures return structured errors.
- The codebase is ready for Phase 3 frontend integration.

Start by inspecting the repository and identifying the current engine interfaces.
Then propose the minimal API design and implement it.
```

## Debugging

```text
We are in Phase 2 of InsightCap, and the API layer is failing or unstable.

Your task:
- inspect the current FastAPI integration carefully
- find the root cause
- fix the issue with minimal architectural damage
- preserve clean separation between engine logic and API logic

Debugging priorities:
- import path or app startup errors
- request parsing failures
- upload handling issues
- engine invocation errors
- serialization problems
- blocking behavior or timeout risks
- bad exception handling

Rules:
- do not move business logic into route handlers unless absolutely necessary
- keep the fix small and coherent
- validate the fix locally if possible
- if streaming was attempted and is unstable, stabilize the non-streaming path first

Output format:
1. Root cause
2. Fix applied
3. Validation result
4. Remaining risk
```

## Succeed

```text
Phase 2 of InsightCap is nearly complete.

Your task:
- review the FastAPI layer against the phase goals
- close the final gaps needed for a stable MVP API
- make sure the engine can be reused by a web frontend without code duplication
- improve only what is necessary for maintainability and Phase 3 readiness

Phase 2 success checklist:
- API starts locally
- POST /analyze works
- response contract is clear
- error handling is consistent
- engine/API boundary is clean
- future streaming or websocket extension is structurally possible

At the end:
- summarize the final API surface
- list exact commands to run the API locally
- mention the main extension points for Phase 3
- mention any known performance or architecture limits
```

## Next Phase

```text
Phase 2 of InsightCap has succeeded.

Now prepare the transition into Phase 3: Web App.

Your task:
- inspect the existing API and engine
- design the simplest frontend that can upload a video, trigger analysis, and display captions
- prefer a fast MVP path first
- keep the UI practical and easy to validate with real users

Phase 3 goals:
- upload UI
- video preview or player
- caption display panel
- export to CSV or JSON if feasible

Before coding:
- summarize the API endpoints and response shape that the frontend will use
- identify whether Streamlit or a custom frontend is the better MVP choice for the current codebase
- propose the smallest implementation plan, then start implementing it
```

