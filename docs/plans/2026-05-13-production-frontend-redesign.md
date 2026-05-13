# InsightCap Production Frontend Redesign Plan

## Summary

Build a new `frontend/` Next.js + TypeScript app. V1 uses dummy/local state only, with no FastAPI integration yet, but preserves the same product workflows: mode selection, uploaded-video analysis UI, RTSP monitoring UI, prompt presets/custom prompts, captions stream, final summary/export, metadata, and session controls.

Superseded note: cleanup berikutnya menghapus UI lama; stack aktif sekarang hanya `frontend/`, `backend/`, dan Docker vLLM.

Use `DESIGN.md` as the visual source of truth: white canvas, near-black ink, sparse emerald CTA, 6px buttons, 8px/12px cards, Inter/Geist-style typography, subtle hairlines, and product-UI mockups instead of dark industrial styling.

## Key Changes

- Create `frontend/` with Next.js App Router, TypeScript, Tailwind, ESLint, and `lucide-react`.
- Build a single app route with client-side interaction because V1 is a dummy prototype.
- Add mode selection, app shell, control rail, preview/captions workspace, and metadata strip.
- Preserve video and RTSP feature parity with local dummy data.
- Keep backend untouched and reserve `NEXT_PUBLIC_INSIGHTCAP_API_BASE_URL` for later integration.
- Update README with new frontend commands.

## Implementation

- Scaffold `frontend/` manually with Next.js App Router config and Tailwind.
- Add reusable UI primitives and focused components for app shell, controls, workspaces, captions, metadata, prompts, status, and buttons.
- Add prompt presets into frontend constants.
- Implement simulated video analysis and RTSP event loops with local state only.
- Add Playwright smoke tests for mode selection, video flow, RTSP flow, and responsive viewports.

## Test Plan

- `cd frontend && npm run lint`
- `cd frontend && npm run build`
- `cd frontend && npm run test:e2e`
- Existing Python tests remain unchanged.

## Assumptions

- Next.js TypeScript is approved.
- `frontend/` is the new production UI directory.
- V1 is dummy-only before backend integration.
- `DESIGN.md` overrides generic UI guidance where they conflict.
