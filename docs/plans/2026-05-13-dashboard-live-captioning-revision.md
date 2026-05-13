# Dashboard Live Captioning Revision Plan

## Summary

Make the new Next.js frontend open directly to the Live Captioning dashboard instead of a marketing-style mode selector. Keep all behavior mocked/local-only before backend integration.

Superseded note: cleanup berikutnya menghapus UI lama; stack aktif sekarang hanya `frontend/`, `backend/`, dan Docker vLLM.

## Key Changes

- Default first screen is Video Analysis dashboard.
- Move Video/RTSP selection into compact header mode tabs.
- Add persistent light/dark theme toggle using `localStorage`.
- Trim marketing copy and keep dashboard labels operational.
- Preserve expected video and RTSP flows with local mock data.

## Test Plan

- `cd frontend && npm run lint`
- `cd frontend && npm run build`
- `cd frontend && npm run test:e2e`

## Assumptions

- Existing mock data remains the source for frontend behavior.
- Theme defaults to saved user preference or light mode.
