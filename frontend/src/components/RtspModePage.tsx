"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { RTSP_PROMPT_PRESETS } from "@/data/prompts";
import { RTSP_SAMPLE_CAPTIONS } from "@/lib/dummy-data";
import type { CaptionRow, RtspMetadata, RtspStatus, Theme } from "@/lib/types";
import { ControlDrawer } from "./ControlDrawer";
import { PageHeader } from "./PageHeader";
import { RtspControls } from "./RtspControls";
import { RtspWorkspace } from "./RtspWorkspace";

const DEFAULT_MODEL = "qwen3.5:0.8b";

export function RtspModePage({ theme, onThemeChange }: { theme: Theme; onThemeChange: (t: Theme) => void }) {
  const router = useRouter();

  const [model, setModel] = useState(DEFAULT_MODEL);
  const [rtspUrl, setRtspUrl] = useState("");
  const [rtspSessionName, setRtspSessionName] = useState("");
  const [sampleEverySeconds, setSampleEverySeconds] = useState(1);
  const [rtspStatus, setRtspStatus] = useState<RtspStatus>("idle");
  const [rtspCaptions, setRtspCaptions] = useState<CaptionRow[]>([]);
  const [rtspPreset, setRtspPreset] = useState("default");
  const [rtspCustomPrompt, setRtspCustomPrompt] = useState(false);
  const [rtspFramePrompt, setRtspFramePrompt] = useState(
    RTSP_PROMPT_PRESETS.default.framePrompt,
  );

  useEffect(() => {
    if (rtspStatus !== "live") return;

    let index = rtspCaptions.length;
    const interval = window.setInterval(() => {
      const sample = RTSP_SAMPLE_CAPTIONS[index % RTSP_SAMPLE_CAPTIONS.length];
      setRtspCaptions((current) => [
        ...current.slice(-39),
        {
          ...sample,
          id: `${sample.id}-${Date.now()}`,
          frame: current.length + 1,
          meta: sample.kind === "caption" ? `LAG ${118 + (current.length % 8) * 7} ms` : sample.meta,
        },
      ]);
      index += 1;
    }, Math.max(700, sampleEverySeconds * 1000));

    return () => window.clearInterval(interval);
  }, [rtspCaptions.length, rtspStatus, sampleEverySeconds]);

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

  function toggleRtspSimulation() {
    const live = rtspStatus === "live" || rtspStatus === "connecting";

    if (live) {
      setRtspStatus("stopped");
      setRtspCaptions((current) => [
        ...current,
        {
          id: `rtsp-stopped-${Date.now()}`,
          frame: current.length + 1,
          caption: "RTSP session stopped locally.",
          kind: "system",
        },
      ]);
      return;
    }

    setRtspStatus("connecting");
    setRtspCaptions([]);
    window.setTimeout(() => {
      setRtspStatus("live");
      setRtspCaptions([RTSP_SAMPLE_CAPTIONS[0]]);
    }, 700);
  }

  function handleBack() {
    const live = rtspStatus === "live" || rtspStatus === "connecting";
    if (live) {
      const confirmed = window.confirm("RTSP monitoring is active. Stop monitoring and go back?");
      if (!confirmed) return;
      setRtspStatus("stopped");
    }
    router.push("/");
  }

  const rtspMetadata: RtspMetadata = {
    status: rtspStatus,
    captionsEmitted: rtspCaptions.filter((c) => c.kind !== "system").length,
    lagMs: rtspStatus === "live" ? 132 : null,
    modelId: model,
    reconnectCount: 0,
  };

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
              onToggleRtsp={toggleRtspSimulation}
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
          captions={rtspCaptions}
          metadata={rtspMetadata}
        />
      </section>

      <footer className="mx-auto w-full max-w-[1440px] px-5 pb-6 font-mono text-xs text-ink-muted md:px-8">
        Mock data active. Backend integration pending.
      </footer>
    </main>
  );
}
