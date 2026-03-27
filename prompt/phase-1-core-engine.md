# Phase 1 Prompt

## Start Phase

```text
You are helping me build Phase 1 of InsightCap.

Project name: InsightCap
Phase: Core Python Engine
Development machine: Apple Silicon M4
Project language: English

Product context:
- InsightCap is a video captioning and video understanding system.
- It should analyze local video files and produce useful text captions.
- The architecture target is Engine -> API -> Web.
- For development, optimize for macOS Apple Silicon.
- For future production, keep the code portable to Linux + NVIDIA GPU.

Your task in this phase:
- Set up the initial project structure for the core engine.
- Build the video loading and frame sampling pipeline using OpenCV.
- Add device detection with priority mps -> cuda -> cpu.
- Prepare an inference abstraction that can work in development on Apple Silicon and later be adapted for production inference runtimes.
- Add a prompt-building layer for video frame understanding.
- Add a CLI entrypoint that accepts a local video path and prints the generated caption.

Important implementation constraints:
- Use Python 3.10+.
- Keep the code modular and production-oriented.
- Prefer clean package boundaries instead of a single script.
- Do not assume vLLM is available on Apple Silicon.
- Use English for code, docs, comments, variables, filenames, and outputs.
- Avoid overengineering; build a working MVP first.

Expected deliverables:
- project structure for the core engine
- video reader module
- frame sampler module
- device detection module
- caption pipeline skeleton
- CLI command
- basic README or usage notes if needed

Definition of done:
- I can run a CLI command against a local short video.
- The app loads frames successfully.
- The pipeline reaches caption generation or a clearly defined placeholder inference path.
- The code is structured so Phase 2 API integration can reuse the engine directly.

Work step by step.
Before coding, inspect the repository and propose the minimal implementation plan.
Then implement the code, run relevant checks, and summarize what was built and what remains.
```

## Debugging

```text
We are still in Phase 1 of InsightCap, and the current implementation is failing or incomplete.

Your task:
- Inspect the current repository state carefully.
- Identify the root cause of the failure.
- Fix the issue with the smallest correct change set.
- Preserve the architecture direction of Engine -> API -> Web.
- Keep compatibility with Apple Silicon M4 development.

Debugging priorities:
- broken imports or package structure
- OpenCV video loading issues
- frame extraction logic errors
- wrong device detection for mps/cuda/cpu
- inference interface mismatch
- CLI argument or execution errors
- dependency issues related to macOS Apple Silicon

Rules:
- Do not rewrite the project from scratch unless absolutely necessary.
- Explain the root cause clearly.
- After the fix, run the relevant checks again.
- If something cannot be completed because of environment limits, state that explicitly and leave the code in a clean recoverable state.

Output format:
1. Root cause
2. Fix applied
3. Validation result
4. Remaining risk
```

## Succeed

```text
Phase 1 of InsightCap is nearly complete.

Your task:
- Review the current implementation against the Phase 1 goals.
- Close the last gaps needed to make the core engine usable.
- Improve only what is necessary for reliability and handoff into Phase 2.
- Verify that the project structure, CLI flow, and engine abstraction are stable.

Phase 1 success checklist:
- local video input works
- frame sampling works
- prompt building exists
- device detection exists
- inference path is connected or clearly stubbed
- CLI execution path is documented or obvious
- modules are reusable by a future FastAPI layer

At the end:
- summarize the final Phase 1 state
- list the exact commands to run locally
- list the most important known limitations
- recommend the cleanest entry point for Phase 2
```

## Next Phase

```text
Phase 1 of InsightCap has succeeded.

Now prepare the transition into Phase 2: API Layer and Integration.

Your task:
- Inspect the Phase 1 codebase and reuse the existing engine.
- Design the minimal FastAPI integration around the engine.
- Keep the engine isolated from transport concerns.
- Identify which objects or services should become reusable application services in the API layer.
- Propose the smallest implementation plan for Phase 2, then start implementing it.

Phase 2 goals:
- POST /analyze endpoint
- request/response schema
- upload handling
- streaming-ready architecture if possible
- clean separation between engine and API

Before coding:
- summarize what from Phase 1 is being reused
- identify the interface boundary between engine and API
- call out any blockers that must be fixed first
```

