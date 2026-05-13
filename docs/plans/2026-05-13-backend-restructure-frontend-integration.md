# Backend Restructure + Frontend Integration Plan

## Summary
Buat struktur backend baru di `backend/`, copy dulu logic lama dari `api/` dan `insightcap/`, lalu integrasikan Next.js `frontend/` langsung ke FastAPI. Streamlit `web/` tidak dihapus pada fase ini, tapi dikeluarkan dari workflow utama dan ditandai deprecated.

Runtime target:
- vLLM: `docker compose up vllm`
- API: `uvicorn backend.app.main:app --reload --port 6060`
- Frontend: `cd frontend && npm run dev`
- Frontend URL: `http://localhost:3060`
- API URL: `http://localhost:6060`
- vLLM URL: `http://localhost:8060/v1`

## Backend Structure
Buat package baru:

```text
backend/
├── __init__.py
├── app/
│   ├── main.py
│   ├── dependencies.py
│   ├── api/v1/
│   │   ├── router.py
│   │   └── routes/
│   │       ├── analyze.py
│   │       ├── rtsp.py
│   │       └── system.py
│   ├── schemas/
│   │   ├── video.py
│   │   ├── rtsp.py
│   │   └── system.py
│   └── services/
│       ├── video_analysis.py
│       └── rtsp/
│           ├── manager.py
│           ├── session.py
│           └── utils.py
└── core/
    ├── config.py
    ├── device.py
    ├── pipeline.py
    ├── cli.py
    ├── video/
    ├── inference/
    └── prompt/
```

Endpoint publik tetap sama. vLLM tetap di `docker-compose.yml` root-level, service `vllm`, port `8060`, served model `qwen3.5:0.8b`.

## Implementation Notes
- Copy `api/` dan `insightcap/` ke struktur baru dulu.
- Update import ke `backend.app.*` dan `backend.core.*`.
- Ganti frontend mock simulation dengan FastAPI direct calls via `NEXT_PUBLIC_API_BASE_URL`.
- Streamlit `web/` ditandai legacy/deprecated, tidak dihapus.

## Test Plan
Backend:
```bash
python -m unittest tests/test_vllm_backend.py
python -m unittest tests/test_live_reader.py
python -m unittest tests/test_rtsp_service.py
```

Frontend:
```bash
cd frontend
npm run lint
npm run build
npm run test:e2e
```

Manual smoke:
```bash
docker compose up vllm
curl http://localhost:8060/health
uvicorn backend.app.main:app --reload --port 6060
curl http://localhost:6060/health
cd frontend && npm run dev
```
