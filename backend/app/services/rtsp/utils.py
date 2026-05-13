from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def mask_rtsp_url(url: str) -> str:
    parts = urlsplit(url)
    if not parts.scheme:
        return url
    hostname = parts.hostname or ""
    port = f":{parts.port}" if parts.port else ""
    if parts.username or parts.password:
        netloc = f"***@{hostname}{port}"
    else:
        netloc = f"{hostname}{port}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def mask_error_message(message: str, raw_url: str, safe_url: str) -> str:
    return message.replace(raw_url, safe_url)


def default_session_name(url: str) -> str:
    host = urlsplit(url).hostname or "rtsp-camera"
    return host


# Backward-compatible private names for existing tests/imports during migration.
_utcnow = utcnow
_mask_rtsp_url = mask_rtsp_url
_mask_error_message = mask_error_message
_default_session_name = default_session_name
