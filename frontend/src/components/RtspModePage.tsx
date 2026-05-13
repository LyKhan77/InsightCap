"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { RTSP_PROMPT_PRESETS } from "@/data/prompts";
import {
  createRtspSession,
  deleteRtspSession,
  rtspEventsUrl,
  rtspPreviewMjpegUrl,
  type RtspEvent,
} from "@/lib/api";
import { mapRtspStatus, normalizeRtspEvent } from "@/lib/rtsp-events";
import type { CaptionRow, RtspMetadata, RtspStatus, Theme } from "@/lib/types";
import { AppFooter } from "./AppFooter";
import { ControlDrawer } from "./ControlDrawer";
import { PageHeader } from "./PageHeader";
import { RtspControls } from "./RtspControls";
import { RtspWorkspace } from "./RtspWorkspace";

const DEFAULT_MODEL = "qwen3.5:0.8b";

export function RtspModePage({ theme, onThemeChange }: { theme: Theme; onThemeChange: (t: Theme) => void }) {
  const router = useRouter();
  const sessionIdRef = useRef<string | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);

  const [model, setModel] = useState(DEFAULT_MODEL);
  const [rtspUrl, setRtspUrl] = useState("");
  const [rtspSessionName, setRtspSessionName] = useState("");
  const [sampleEverySeconds, setSampleEverySeconds] = useState(1);
  const [rtspStatus, setRtspStatus] = useState<RtspStatus>("idle");
  const [rtspCaptions, setRtspCaptions] = useState<CaptionRow[]>([]);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewReady, setPreviewReady] = useState(false);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [rtspMetadata, setRtspMetadata] = useState<RtspMetadata>({
    status: "idle",
    captionsEmitted: 0,
    lagMs: null,
    modelId: DEFAULT_MODEL,
    reconnectCount: 0,
  });
  const [rtspPreset, setRtspPreset] = useState("default");
  const [rtspCustomPrompt, setRtspCustomPrompt] = useState(false);
  const [rtspFramePrompt, setRtspFramePrompt] = useState(
    RTSP_PROMPT_PRESETS.default.framePrompt,
  );

  const stopRtspSession = useCallback(async (appendStoppedRow = true) => {
    const sessionId = sessionIdRef.current;
    websocketRef.current?.close();
    websocketRef.current = null;
    sessionIdRef.current = null;
    setPreviewUrl(null);
    setPreviewReady(false);
    setStreamError(null);

    if (sessionId) {
      try {
        await deleteRtspSession(sessionId);
      } catch (error) {
        setRtspCaptions((current) => [
          ...current,
          {
            id: `rtsp-stop-warning-${Date.now()}`,
            frame: current.length + 1,
            caption: error instanceof Error ? error.message : "Failed to stop RTSP session cleanly.",
            kind: "warning",
          },
        ]);
      }
    }

    setRtspStatus("stopped");
    setRtspMetadata((current) => ({ ...current, status: "stopped" }));
    if (appendStoppedRow) {
      setRtspCaptions((current) => [
        ...current,
        {
          id: `rtsp-stopped-local-${Date.now()}`,
          frame: current.length + 1,
          caption: "RTSP session stopped.",
          kind: "system",
        },
      ]);
    }
  }, []);

  useEffect(() => {
    return () => {
      void stopRtspSession(false);
    };
  }, [stopRtspSession]);

  function handlePresetChange(presetName: string) {
    setRtspPreset(presetName);
    if (!rtspCustomPrompt) {
      setRtspFramePrompt(RTSP_PROMPT_PRESETS[presetName].framePrompt);
    }
  }

  function handleCustomPromptChange(enabled: boolean) {
    setRtspCustomPrompt(enabled);
    if (!enabled) {
      setRtspFramePrompt(RTSP_PROMPT_PRESETS[rtspPreset].framePrompt);
    }
  }

  async function toggleRtspMonitoring() {
    const live = rtspStatus === "live" || rtspStatus === "connecting";

    if (live) {
      await stopRtspSession();
      return;
    }

    setRtspStatus("connecting");
    setRtspMetadata({
      status: "connecting",
      captionsEmitted: 0,
      lagMs: null,
      modelId: model,
      reconnectCount: 0,
    });
    setRtspCaptions([]);
    setPreviewUrl(null);
    setPreviewReady(false);
    setStreamError(null);

    try {
      const session = await createRtspSession({
        rtsp_url: rtspUrl,
        model,
        sample_every_seconds: sampleEverySeconds,
        session_name: rtspSessionName.trim() || undefined,
        frame_prompt: rtspFramePrompt,
      });

      sessionIdRef.current = session.session_id;
      const nextStatus = mapRtspStatus(session.status);
      setRtspStatus(nextStatus);
      setRtspMetadata({
        status: nextStatus,
        captionsEmitted: session.captions_emitted,
        lagMs: session.lag_ms,
        modelId: session.model_id,
        reconnectCount: session.reconnect_count,
      });
      setPreviewUrl(rtspPreviewMjpegUrl(session.session_id));

      const socket = new WebSocket(rtspEventsUrl(session.session_id));
      websocketRef.current = socket;
      socket.onmessage = (message) => {
        const event = JSON.parse(message.data) as RtspEvent;
        if (event.event === "connected" || event.event === "caption") {
          setStreamError(null);
        }
        if (event.event === "warning" || event.event === "error") {
          const message = event.data.message;
          setStreamError(typeof message === "string" ? message : "RTSP stream warning received.");
        }
        setRtspCaptions((current) => {
          const normalized = normalizeRtspEvent(event, current.length);
          if (normalized.status) {
            setRtspStatus(normalized.status);
            setRtspMetadata((metadata) => ({ ...metadata, status: normalized.status ?? metadata.status }));
          }
          if (normalized.metadata) {
            setRtspMetadata((metadata) => ({
              ...metadata,
              ...Object.fromEntries(
                Object.entries(normalized.metadata ?? {}).filter(([, value]) => value !== null && value !== undefined),
              ),
            }));
          }
          if (!normalized.row) return current;
          return [...current.slice(-39), normalized.row];
        });
      };
      socket.onerror = () => {
        setStreamError("RTSP event stream connection failed.");
        setRtspCaptions((current) => [
          ...current,
          {
            id: `rtsp-ws-error-${Date.now()}`,
            frame: current.length + 1,
            caption: "RTSP event stream connection failed.",
            kind: "warning",
          },
        ]);
      };
      socket.onclose = () => {
        websocketRef.current = null;
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to start RTSP monitoring.";
      setRtspStatus("stopped");
      setRtspMetadata((current) => ({ ...current, status: "stopped" }));
      setPreviewUrl(null);
      setStreamError(message);
      setRtspCaptions((current) => [
        ...current,
        {
          id: `rtsp-start-error-${Date.now()}`,
          frame: current.length + 1,
          caption: message,
          kind: "warning",
        },
      ]);
    }
  }

  async function handleBack() {
    const live = rtspStatus === "live" || rtspStatus === "connecting";
    if (live) {
      const confirmed = window.confirm("RTSP monitoring is active. Stop monitoring and go back?");
      if (!confirmed) return;
      await stopRtspSession(false);
    }
    router.push("/");
  }

  return (
    <main data-theme={theme} className="flex min-h-screen flex-col bg-canvas text-ink">
      <PageHeader
        modeLabel="RTSP Mode"
        theme={theme}
        onThemeChange={onThemeChange}
        onBack={handleBack}
        controlsTrigger={
          <ControlDrawer title="RTSP Controls">
            <RtspControls
              model={model}
              onModelChange={setModel}
              rtspUrl={rtspUrl}
              onRtspUrlChange={setRtspUrl}
              rtspSessionName={rtspSessionName}
              onRtspSessionNameChange={setRtspSessionName}
              sampleEverySeconds={sampleEverySeconds}
              onSampleEverySecondsChange={setSampleEverySeconds}
              rtspStatus={rtspStatus}
              onToggleRtsp={toggleRtspMonitoring}
              rtspPreset={rtspPreset}
              onRtspPresetChange={handlePresetChange}
              rtspCustomPrompt={rtspCustomPrompt}
              onRtspCustomPromptChange={handleCustomPromptChange}
              rtspFramePrompt={rtspFramePrompt}
              onRtspFramePromptChange={setRtspFramePrompt}
            />
          </ControlDrawer>
        }
      />

      <section className="mx-auto w-full max-w-[1440px] flex-1 px-5 py-6 md:px-8">
        <RtspWorkspace
          sessionName={rtspSessionName}
          source={rtspUrl}
          previewUrl={previewUrl}
          previewReady={previewReady}
          onPreviewReady={() => setPreviewReady(true)}
          streamError={streamError}
          captions={rtspCaptions}
          metadata={rtspMetadata}
        />
      </section>

      <AppFooter />
    </main>
  );
}
