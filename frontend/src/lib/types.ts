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

export type VideoMetadata = {
  frameCount: number;
  durationSeconds: number;
  deviceUsed: string;
  modelId: string;
};

export type RtspMetadata = {
  status: RtspStatus;
  captionsEmitted: number;
  lagMs: number | null;
  modelId: string;
  reconnectCount: number;
};
