import type { RtspEvent } from "./api";
import type { CaptionRow, RtspMetadata, RtspStatus } from "./types";

type NormalizedRtspEvent = {
  row?: CaptionRow;
  metadata?: Partial<RtspMetadata>;
  status?: RtspStatus;
};

export function normalizeRtspEvent(event: RtspEvent, currentCount: number): NormalizedRtspEvent {
  const data = event.data;

  if (event.event === "connected") {
    const width = numberValue(data.width);
    const height = numberValue(data.height);
    const fps = numberValue(data.fps);
    return {
      status: "live",
      row: {
        id: `rtsp-connected-${event.emitted_at ?? Date.now()}`,
        frame: currentCount + 1,
        caption: "Camera connected and preview bridge is receiving frames.",
        meta: width && height ? `${width}x${height} - ${fps ?? 0} FPS` : undefined,
        kind: "system",
      },
    };
  }

  if (event.event === "caption") {
    const seq = numberValue(data.seq) ?? currentCount + 1;
    const lagMs = numberValue(data.lag_ms);
    return {
      row: {
        id: `rtsp-caption-${seq}-${event.emitted_at ?? Date.now()}`,
        frame: seq,
        caption: stringValue(data.caption) ?? "",
        meta: lagMs === null ? undefined : `LAG ${lagMs} ms`,
        kind: "caption",
      },
      metadata: {
        captionsEmitted: seq,
        lagMs,
      },
    };
  }

  if (event.event === "heartbeat") {
    const status = mapRtspStatus(stringValue(data.status));
    return {
      status,
      metadata: {
        status,
        ...(numberValue(data.captions_emitted) === null
          ? {}
          : { captionsEmitted: numberValue(data.captions_emitted) as number }),
        ...(numberValue(data.reconnect_count) === null
          ? {}
          : { reconnectCount: numberValue(data.reconnect_count) as number }),
        lagMs: numberValue(data.lag_ms),
      },
    };
  }

  if (event.event === "warning") {
    return {
      status: "connecting",
      row: {
        id: `rtsp-warning-${event.emitted_at ?? Date.now()}`,
        frame: currentCount + 1,
        caption: stringValue(data.message) ?? "RTSP warning received.",
        kind: "warning",
      },
      metadata: {
        ...(numberValue(data.reconnect_count) === null
          ? {}
          : { reconnectCount: numberValue(data.reconnect_count) as number }),
      },
    };
  }

  if (event.event === "stopped") {
    return {
      status: "stopped",
      row: {
        id: `rtsp-stopped-${event.emitted_at ?? Date.now()}`,
        frame: currentCount + 1,
        caption: "RTSP session stopped.",
        kind: "system",
      },
      metadata: { status: "stopped" },
    };
  }

  if (event.event === "error") {
    return {
      status: "stopped",
      row: {
        id: `rtsp-error-${event.emitted_at ?? Date.now()}`,
        frame: currentCount + 1,
        caption: stringValue(data.message) ?? "RTSP event stream error.",
        kind: "warning",
      },
    };
  }

  return {};
}

export function mapRtspStatus(status: string | null | undefined): RtspStatus {
  if (status === "running") return "live";
  if (status === "connecting" || status === "starting") return "connecting";
  if (status === "stopped" || status === "stopping") return "stopped";
  return "idle";
}

function stringValue(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function numberValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}
