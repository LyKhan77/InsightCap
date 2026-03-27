# Phase 3 Prompt

## Start Phase

```text
You are helping me build Phase 3 of InsightCap.

Project name: InsightCap
Phase: Web App
Development machine: Apple Silicon M4
Project language: English

Context:
- InsightCap already has a core engine and an API layer.
- This phase should deliver a usable browser-based interface.
- The first goal is a practical MVP, not a design-heavy product.

Your task in this phase:
- build the web interface for InsightCap
- allow users to upload a local video
- call the analysis flow
- show the analysis result in a clear readable way
- provide a path for exporting results if feasible

Preferred direction:
- use Streamlit for MVP unless the repository already justifies a custom frontend
- keep the UI simple, reliable, and demonstrable
- make the frontend clearly reusable for later refinement

Constraints:
- use English in UI labels, docs, code, and naming
- preserve compatibility with the existing API and engine
- avoid mixing experimental frontend complexity into the MVP unless required

Definition of done:
- I can launch the web app locally
- I can upload a short video
- I can trigger analysis and see the result in the browser
- the UX is clear enough for stakeholder demo use

Start by inspecting the repository and current API surface.
Then propose the smallest UI implementation plan and build it.
```

## Debugging

```text
We are in Phase 3 of InsightCap, and the web app is failing or not usable.

Your task:
- inspect the current frontend implementation and its integration with the API/engine
- identify the root cause
- fix the issue with the smallest coherent change
- preserve a simple MVP-first architecture

Debugging priorities:
- app startup issues
- broken upload flow
- failed API calls
- wrong response parsing
- UI not showing captions correctly
- file handling issues
- export action failures

Rules:
- do not redesign the entire frontend unless necessary
- prioritize working upload -> analyze -> display flow
- keep the UI implementation consistent with the existing stack choice
- validate the user flow after fixing

Output format:
1. Root cause
2. Fix applied
3. Validation result
4. Remaining risk
```

## Succeed

```text
Phase 3 of InsightCap is nearly complete.

Your task:
- review the web app against the phase goals
- close the final usability gaps for the MVP
- improve only what is necessary for a stable demo-ready release

Phase 3 success checklist:
- web app launches locally
- upload flow works
- caption result is visible and readable
- integration with the underlying analysis flow works
- the app is easy to demo without backend confusion

At the end:
- summarize the final user flow
- list exact commands to run the app locally
- mention known UX or performance limitations
- identify what would come after MVP if we continue
```

## Next Phase

```text
Phase 3 of InsightCap has succeeded.

Now prepare the project for post-MVP hardening.

Your task:
- inspect the full codebase across engine, API, and web
- identify the highest-value next steps for production readiness
- propose a prioritized roadmap for stability, performance, observability, testing, and deployment

Focus areas:
- model/runtime strategy refinement
- production inference on Linux + NVIDIA
- queueing and concurrency
- live captioning over streaming/WebSocket
- tests and validation
- Dockerization and deployment
- logging and monitoring

Before making changes:
- summarize the current MVP state
- identify the weakest architectural point
- propose the smallest next milestone with the highest practical value
```

