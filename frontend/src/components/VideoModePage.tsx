"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { VIDEO_PROMPT_PRESETS } from "@/data/prompts";
import { DUMMY_SUMMARY, VIDEO_SAMPLE_CAPTIONS } from "@/lib/dummy-data";
import type { CaptionRow, Theme, VideoMetadata, VideoStatus } from "@/lib/types";
import { ControlDrawer } from "./ControlDrawer";
import { PageHeader } from "./PageHeader";
import { VideoControls } from "./VideoControls";
import { VideoWorkspace } from "./VideoWorkspace";

const DEFAULT_MODEL = "qwen3.5:0.8b";

export function VideoModePage({ theme, onThemeChange }: { theme: Theme; onThemeChange: (t: Theme) => void }) {
  const router = useRouter();

  const [model, setModel] = useState(DEFAULT_MODEL);
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoStatus, setVideoStatus] = useState<VideoStatus>("idle");
  const [videoCaptions, setVideoCaptions] = useState<CaptionRow[]>([]);
  const [finalCaption, setFinalCaption] = useState<string | null>(null);
  const [videoPreset, setVideoPreset] = useState("default");
  const [videoCustomPrompts, setVideoCustomPrompts] = useState(false);
  const [videoFramePrompt, setVideoFramePrompt] = useState(
    VIDEO_PROMPT_PRESETS.default.framePrompt,
  );
  const [videoSummaryPrompt, setVideoSummaryPrompt] = useState(
    VIDEO_PROMPT_PRESETS.default.summaryPrompt,
  );

  const fileUrl = useMemo(() => {
    if (!videoFile) return null;
    return URL.createObjectURL(videoFile);
  }, [videoFile]);

  useEffect(() => {
    return () => {
      if (fileUrl) URL.revokeObjectURL(fileUrl);
    };
  }, [fileUrl]);

  function handleVideoFileChange(file: File | null) {
    setVideoFile(file);
    setVideoStatus(file ? "ready" : "idle");
    setVideoCaptions([]);
    setFinalCaption(null);
  }

  function handlePresetChange(presetName: string) {
    setVideoPreset(presetName);
    if (!videoCustomPrompts) {
      const preset = VIDEO_PROMPT_PRESETS[presetName];
      setVideoFramePrompt(preset.framePrompt);
      setVideoSummaryPrompt(preset.summaryPrompt);
    }
  }

  function handleCustomPromptsChange(enabled: boolean) {
    setVideoCustomPrompts(enabled);
    if (!enabled) {
      const preset = VIDEO_PROMPT_PRESETS[videoPreset];
      setVideoFramePrompt(preset.framePrompt);
      setVideoSummaryPrompt(preset.summaryPrompt);
    }
  }

  function startVideoSimulation() {
    if (!videoFile || videoStatus === "analyzing") return;

    setVideoStatus("initializing");
    setVideoCaptions([]);
    setFinalCaption(null);

    window.setTimeout(() => {
      setVideoStatus("analyzing");
      VIDEO_SAMPLE_CAPTIONS.forEach((caption, index) => {
        window.setTimeout(() => {
          setVideoCaptions((current) => [...current, caption]);
          if (index === VIDEO_SAMPLE_CAPTIONS.length - 1) {
            window.setTimeout(() => {
              setFinalCaption(DUMMY_SUMMARY);
              setVideoStatus("complete");
            }, 650);
          }
        }, index * 650);
      });
    }, 650);
  }

  const videoMetadata: VideoMetadata = {
    frameCount: videoCaptions.length,
    durationSeconds: videoFile ? 4.8 : 0,
    deviceUsed: "dummy",
    modelId: model,
  };

  return (
    <main data-theme={theme} className="flex min-h-screen flex-col bg-canvas text-ink">
      <PageHeader
        modeLabel="Video Mode"
        theme={theme}
        onThemeChange={onThemeChange}
        onBack={() => router.push("/")}
        controlsTrigger={
          <ControlDrawer title="Video Controls">
            <VideoControls
              model={model}
              onModelChange={setModel}
              videoFileName={videoFile?.name ?? null}
              onVideoFileChange={handleVideoFileChange}
              videoStatus={videoStatus}
              onStartVideo={startVideoSimulation}
              videoPreset={videoPreset}
              onVideoPresetChange={handlePresetChange}
              videoCustomPrompts={videoCustomPrompts}
              onVideoCustomPromptsChange={handleCustomPromptsChange}
              videoFramePrompt={videoFramePrompt}
              onVideoFramePromptChange={setVideoFramePrompt}
              videoSummaryPrompt={videoSummaryPrompt}
              onVideoSummaryPromptChange={setVideoSummaryPrompt}
            />
          </ControlDrawer>
        }
      />

      <section className="mx-auto w-full max-w-[1440px] flex-1 px-5 py-6 md:px-8">
        <VideoWorkspace
          fileName={videoFile?.name ?? null}
          fileUrl={fileUrl}
          status={videoStatus}
          captions={videoCaptions}
          finalCaption={finalCaption}
          metadata={videoMetadata}
        />
      </section>

      <footer className="mx-auto w-full max-w-[1440px] px-5 pb-6 font-mono text-xs text-ink-muted md:px-8">
        Mock data active. Backend integration pending.
      </footer>
    </main>
  );
}
