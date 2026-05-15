import type { AutoLabelConfig, AutoLabelStatus } from "./types";
import { autoLabelPayload, normalizeAutoLabelStatus } from "./auto-label";

export const API_BASE_URL = resolveApiBaseUrl();

function resolveApiBaseUrl() {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "");
  if (configured) return configured;
  if (typeof window !== "undefined") {
    return `${window.location.protocol}//${window.location.hostname}:6060`;
  }
  return "http://localhost:6060";
}

function apiUrl(path: string) {
  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

function wsUrl(path: string) {
  const url = new URL(apiUrl(path));
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return url.toString();
}

export type RtspSessionResponse = {
  session_id: string;
  session_name: string;
  status: string;
  source: string;
  model_id: string;
  sample_every_seconds: number;
  started_at: string | null;
  last_event_at: string | null;
  last_caption: string | null;
  captions_emitted: number;
  reconnect_count: number;
  lag_ms: number | null;
  last_error: string | null;
  auto_label?: unknown;
};

export type RtspSessionCreateRequest = {
  rtsp_url: string;
  model: string;
  sample_every_seconds: number;
  session_name?: string;
  frame_prompt?: string;
  auto_label?: ReturnType<typeof autoLabelPayload>;
};

export type RtspEvent = {
  event: string;
  session_id: string;
  emitted_at: string | null;
  data: Record<string, unknown>;
};

export type HealthResponse = {
  status: string;
  device: string;
  backend: string;
  vllm: {
    status: string;
    base_url: string;
    error?: string;
  };
};

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(apiUrl("/health"), { cache: "no-store" });
  if (!response.ok) {
    throw new Error(await readApiError(response));
  }
  return response.json();
}

export function analyzeStreamUrl() {
  return apiUrl("/api/v1/analyze/stream");
}

export function autoLabelOverlayUrl(path: string) {
  return apiUrl(`/api/v1/auto-label/overlay?path=${encodeURIComponent(path)}`);
}

export async function createRtspSession(
  request: RtspSessionCreateRequest,
): Promise<RtspSessionResponse> {
  const response = await fetch(apiUrl("/api/v1/rtsp/sessions"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(await readApiError(response));
  }

  return response.json();
}

export async function startRtspAutoLabel(
  sessionId: string,
  config: AutoLabelConfig,
): Promise<AutoLabelStatus> {
  const response = await fetch(apiUrl(`/api/v1/rtsp/sessions/${sessionId}/auto-label/start`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(autoLabelPayload(config)),
  });

  if (!response.ok) {
    throw new Error(await readApiError(response));
  }

  return normalizeAutoLabelStatus(await response.json());
}

export async function stopRtspAutoLabel(sessionId: string): Promise<AutoLabelStatus> {
  const response = await fetch(apiUrl(`/api/v1/rtsp/sessions/${sessionId}/auto-label/stop`), {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(await readApiError(response));
  }

  return normalizeAutoLabelStatus(await response.json());
}

export async function deleteRtspSession(sessionId: string): Promise<RtspSessionResponse> {
  const response = await fetch(apiUrl(`/api/v1/rtsp/sessions/${sessionId}`), {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error(await readApiError(response));
  }

  return response.json();
}

export function rtspPreviewMjpegUrl(sessionId: string) {
  return apiUrl(`/api/v1/rtsp/sessions/${sessionId}/preview.mjpeg`);
}

export function rtspEventsUrl(sessionId: string) {
  return wsUrl(`/api/v1/rtsp/sessions/${sessionId}/events`);
}

async function readApiError(response: Response) {
  try {
    const payload = await response.json();
    if (typeof payload.detail === "string") return payload.detail;
    return JSON.stringify(payload);
  } catch {
    return `${response.status} ${response.statusText}`.trim();
  }
}
