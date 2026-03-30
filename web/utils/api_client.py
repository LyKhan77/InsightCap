"""API client for InsightCap web interface."""
from __future__ import annotations

import json
from urllib.parse import urlparse
import requests
from typing import Generator, Dict, Any


API_BASE_URL = "http://localhost:6060"


class InsightCapAPIError(Exception):
    """API communication error."""
    pass


class APIClient:
    """Client for InsightCap API."""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def _ws_base_url(self) -> str:
        parsed = urlparse(self.base_url)
        scheme = "wss" if parsed.scheme == "https" else "ws"
        return f"{scheme}://{parsed.netloc}"

    def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            raise InsightCapAPIError("Cannot connect to API. Is it running at localhost:6060?")
        except requests.exceptions.Timeout:
            raise InsightCapAPIError("API health check timed out.")
        except Exception as e:
            raise InsightCapAPIError(f"Health check failed: {str(e)}")

    def analyze_stream(
        self,
        video_path: str,
        model: str = "qwen3.5:0.8b"
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream analysis results via SSE."""
        with open(video_path, "rb") as f:
            files = {"file": f}
            data = {"model": model}

            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/analyze/stream",
                    files=files,
                    data=data,
                    stream=True,
                    timeout=300
                )
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        decoded = line.decode("utf-8")
                        if decoded.startswith("data: "):
                            try:
                                event_data = json.loads(decoded[6:])
                                yield event_data
                            except json.JSONDecodeError:
                                continue

            except requests.exceptions.ConnectionError:
                raise InsightCapAPIError("Cannot connect to API. Is it running?")
            except requests.exceptions.Timeout:
                raise InsightCapAPIError("Analysis request timed out.")
            except Exception as e:
                raise InsightCapAPIError(f"Analysis failed: {str(e)}")

    def analyze(
        self,
        video_path: str,
        model: str = "qwen3.5:0.8b"
    ) -> Dict[str, Any]:
        """Non-streaming analysis."""
        with open(video_path, "rb") as f:
            files = {"file": f}
            data = {"model": model}

            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/analyze",
                    files=files,
                    data=data,
                    timeout=300
                )
                response.raise_for_status()
                return response.json()

            except requests.exceptions.ConnectionError:
                raise InsightCapAPIError("Cannot connect to API. Is it running?")
            except requests.exceptions.Timeout:
                raise InsightCapAPIError("Analysis request timed out.")
            except Exception as e:
                raise InsightCapAPIError(f"Analysis failed: {str(e)}")

    def create_rtsp_session(
        self,
        rtsp_url: str,
        model: str = "qwen3.5:0.8b",
        sample_every_seconds: float = 1.0,
        session_name: str | None = None,
    ) -> Dict[str, Any]:
        """Create and start a new RTSP monitoring session."""
        payload: Dict[str, Any] = {
            "rtsp_url": rtsp_url,
            "model": model,
            "sample_every_seconds": sample_every_seconds,
        }
        if session_name:
            payload["session_name"] = session_name

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/rtsp/sessions",
                json=payload,
                timeout=15,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            raise InsightCapAPIError("Cannot connect to API. Is it running?")
        except requests.exceptions.Timeout:
            raise InsightCapAPIError("RTSP session creation timed out.")
        except Exception as e:
            raise InsightCapAPIError(f"RTSP session creation failed: {str(e)}")

    def list_rtsp_sessions(self) -> Dict[str, Any]:
        """Return the current RTSP session list."""
        try:
            response = requests.get(f"{self.base_url}/api/v1/rtsp/sessions", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            raise InsightCapAPIError("Cannot connect to API. Is it running?")
        except requests.exceptions.Timeout:
            raise InsightCapAPIError("RTSP session list request timed out.")
        except Exception as e:
            raise InsightCapAPIError(f"RTSP session list failed: {str(e)}")

    def get_rtsp_session(self, session_id: str) -> Dict[str, Any]:
        """Return one RTSP session snapshot."""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/rtsp/sessions/{session_id}",
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            raise InsightCapAPIError("Cannot connect to API. Is it running?")
        except requests.exceptions.Timeout:
            raise InsightCapAPIError("RTSP session status request timed out.")
        except Exception as e:
            raise InsightCapAPIError(f"RTSP session status failed: {str(e)}")

    def delete_rtsp_session(self, session_id: str) -> Dict[str, Any]:
        """Stop one RTSP session."""
        try:
            response = requests.delete(
                f"{self.base_url}/api/v1/rtsp/sessions/{session_id}",
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            raise InsightCapAPIError("Cannot connect to API. Is it running?")
        except requests.exceptions.Timeout:
            raise InsightCapAPIError("RTSP session deletion timed out.")
        except Exception as e:
            raise InsightCapAPIError(f"RTSP session deletion failed: {str(e)}")

    def rtsp_preview_stream_url(self, session_id: str) -> str:
        """Return the MJPEG preview URL for one RTSP session."""
        return f"{self.base_url}/api/v1/rtsp/sessions/{session_id}/preview.mjpeg"

    def rtsp_events_ws_url(self, session_id: str) -> str:
        """Return the WebSocket event URL for one RTSP session."""
        return f"{self._ws_base_url()}/api/v1/rtsp/sessions/{session_id}/events"
