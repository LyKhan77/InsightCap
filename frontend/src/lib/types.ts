export type Mode = "video" | "rtsp";

export type Theme = "light" | "dark";

export type CaptionRow = {
  id: string;
  frame: number;
  caption: string;
  meta?: string;
  kind?: "caption" | "system" | "warning";
  timestampStart?: number;
  timestampEnd?: number;
};

export type VideoStatus = "idle" | "ready" | "initializing" | "analyzing" | "complete";

export type RtspStatus = "idle" | "connecting" | "live" | "stopped";

export type AutoLabelStatus = {
  status: "idle" | "active" | "draining" | "done" | "error";
  datasetPath: string | null;
  latestOverlayPath: string | null;
  framesLabelled: number;
  framesDropped: number;
  chunksEnqueued: number;
  remainingSeconds: number | null;
  lastError: string | null;
};

export type AutoLabelConfig = {
  enabled: boolean;
  prompt: string;
  scheduleMode: "duration" | "automatic";
  durationMinutes: number;
  confidence: number;
  model: string;
};

export type VideoMetadata = {
  frameCount: number;
  durationSeconds: number;
  deviceUsed: string;
  modelId: string;
  autoLabel: AutoLabelStatus;
};

export type RtspMetadata = {
  status: RtspStatus;
  captionsEmitted: number;
  lagMs: number | null;
  modelId: string;
  reconnectCount: number;
  autoLabel: AutoLabelStatus;
};
