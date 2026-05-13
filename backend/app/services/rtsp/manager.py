from __future__ import annotations

import asyncio
import threading
from uuid import uuid4

from backend.app.schemas.rtsp import RTSPSessionCreateRequest, RTSPSessionResponse
from backend.app.services.rtsp.session import RtspSession


class RtspSessionService:
    """Registry and lifecycle manager for RTSP monitoring sessions."""

    def __init__(self, max_active_sessions: int = 2) -> None:
        self.max_active_sessions = max_active_sessions
        self._lock = threading.RLock()
        self._sessions: dict[str, RtspSession] = {}

    def create_session(self, request: RTSPSessionCreateRequest) -> RTSPSessionResponse:
        with self._lock:
            active = sum(
                1
                for session in self._sessions.values()
                if session.snapshot().status not in {"stopped"}
            )
            if active >= self.max_active_sessions:
                raise RuntimeError(
                    f"Maximum active RTSP sessions reached ({self.max_active_sessions})."
                )

            session_id = uuid4().hex
            session = RtspSession(session_id, request)
            self._sessions[session_id] = session

        session.start()
        return session.snapshot()

    def get_session(self, session_id: str) -> RtspSession:
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"Unknown RTSP session: {session_id}")
        return session

    def list_sessions(self) -> list[RTSPSessionResponse]:
        with self._lock:
            sessions = list(self._sessions.values())
        return [session.snapshot() for session in sessions]

    def delete_session(self, session_id: str) -> RTSPSessionResponse:
        with self._lock:
            session = self._sessions.pop(session_id, None)
        if session is None:
            raise KeyError(f"Unknown RTSP session: {session_id}")
        session.stop()
        return session.snapshot()

    async def subscribe(self, session_id: str) -> tuple[RtspSession, str, asyncio.Queue]:
        session = self.get_session(session_id)
        subscriber_id, queue = await session.subscribe()
        return session, subscriber_id, queue

    def unsubscribe(self, session_id: str, subscriber_id: str) -> None:
        try:
            session = self.get_session(session_id)
        except KeyError:
            return
        session.unsubscribe(subscriber_id)

    def shutdown(self) -> None:
        with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for session in sessions:
            session.stop()


rtsp_session_service = RtspSessionService()
