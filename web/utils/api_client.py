"""API client for InsightCap web interface."""
from __future__ import annotations

import json
import requests
from typing import Optional, Generator, Dict, Any


API_BASE_URL = "http://localhost:6060"


class InsightCapAPIError(Exception):
    """API communication error."""
    pass


class APIClient:
    """Client for InsightCap API."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")
    
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
