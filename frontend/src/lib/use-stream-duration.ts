import { useEffect, useRef, useState } from "react";
import type { RtspStatus } from "./types";

export function useStreamDuration(status: RtspStatus): string {
  const [elapsed, setElapsed] = useState(0);
  const startRef = useRef<number | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (status === "live" && startRef.current === null) {
      startRef.current = Date.now();
    }

    if (status === "live") {
      intervalRef.current = setInterval(() => {
        if (startRef.current !== null) {
          setElapsed(Math.floor((Date.now() - startRef.current) / 1000));
        }
      }, 1000);
    }

    return () => {
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      if (status === "stopped" || status === "idle") {
        startRef.current = null;
        setElapsed(0);
      }
    };
  }, [status]);

  return formatDuration(elapsed);
}

function formatDuration(totalSeconds: number): string {
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  const mm = String(m).padStart(2, "0");
  const ss = String(s).padStart(2, "0");
  if (h > 0) {
    return `${String(h).padStart(2, "0")}:${mm}:${ss}`;
  }
  return `${mm}:${ss}`;
}
