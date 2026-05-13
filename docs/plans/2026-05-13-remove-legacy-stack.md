# Remove Legacy Stack

## Summary
- Remove legacy `api/`, `insightcap/`, and `web/` directories.
- Keep the supported stack focused on Next.js `frontend/`, FastAPI `backend/`, and Docker vLLM.
- Update Markdown documentation so old folders and Streamlit workflow are no longer presented as supported paths.

## Implementation
- Delete legacy source directories and Python cache files inside them.
- Remove `streamlit` from `requirements.txt`.
- Update `README.md`, `ARCHITECTURE.md`, and `AGENTS.md` references to reflect the active stack only.
- Verify no stale legacy entrypoint references remain in active docs/code.

## Verification
- Search for `api.main`, `insightcap`, `streamlit`, `web/`, and `python -m insightcap`.
- Smoke import `backend.app.main` and `backend.core.pipeline`.
- Run Python and frontend checks where local dependencies are available.
