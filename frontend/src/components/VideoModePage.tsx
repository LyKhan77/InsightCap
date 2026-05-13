"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { VIDEO_PROMPT_PRESETS } from "@/data/prompts";
import type { CaptionRow, Theme, VideoMetadata, VideoStatus } from "@/lib/types";
import { streamVideoAnalysis } from "@/lib/video-stream";
import { AppFooter } from "./AppFooter";
import { ControlDrawer } from "./ControlDrawer";
import { PageHeader } from "./PageHeader";
import { VideoControls } from "./VideoControls";
import { VideoWorkspace } from "./VideoWorkspace";

const DEFAULT_MODEL = "qwen3.5:0.8b";

export function VideoModePage({ theme, onThemeChange }: { theme: Theme; onThemeChange: (t: Theme) => void }) {
  const router = useRouter();
  const abortControllerRef = useRef<AbortController | null>(null);

  const [model, setModel] = useState(DEFAULT_MODEL);
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoStatus, setVideoStatus] = useState<VideoStatus>("idle");
  const [videoCaptions, setVideoCaptions] = useState<CaptionRow[]>([]);
  const [finalCaption, setFinalCaption] = useState<string | null>(null);
  const [videoMetadata, setVideoMetadata] = useState<VideoMetadata>({
    frameCount: 0,
    durationSeconds: 0,
    deviceUsed: "--",
    modelId: DEFAULT_MODEL,
  });
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

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  function handleVideoFileChange(file: File | null) {
    abortControllerRef.current?.abort();
    setVideoFile(file);
    setVideoStatus(file ? "ready" : "idle");
    setVideoCaptions([]);
    setFinalCaption(null);
    setVideoMetadata({
      frameCount: 0,
      durationSeconds: 0,
      deviceUsed: "--",
      modelId: model,
    });
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

  async function startVideoAnalysis() {
    if (!videoFile || videoStatus === "analyzing") return;

    const controller = new AbortController();
    abortControllerRef.current = controller;
    setVideoStatus("initializing");
    setVideoCaptions([]);
    setFinalCaption(null);
    setVideoMetadata({
      frameCount: 0,
      durationSeconds: 0,
      deviceUsed: "--",
      modelId: model,
    });

    try {
      await streamVideoAnalysis({
        file: videoFile,
        model,
        framePrompt: videoFramePrompt,
        summaryPrompt: videoSummaryPrompt,
        signal: controller.signal,
        onEvent: (event) => {
          if (event.event === "init") {
            setVideoStatus("analyzing");
            setVideoMetadata((current) => ({
              ...current,
              frameCount: event.data.total_frames,
              durationSeconds: event.data.duration_seconds,
            }));
          }

          if (event.event === "frame") {
            setVideoCaptions((current) => [
              ...current,
              {
                id: `video-frame-${event.data.index}-${Date.now()}`,
                frame: event.data.index + 1,
                caption: event.data.caption,
                meta: `${event.data.timestamp_seconds.toFixed(1)}s`,
                kind: "caption",
              },
            ]);
          }

          if (event.event === "summary") {
            setFinalCaption(event.data.caption);
          }

          if (event.event === "done") {
            setVideoMetadata({
              frameCount: event.data.frame_count,
              durationSeconds: event.data.duration_seconds,
              deviceUsed: event.data.device_used,
              modelId: event.data.model_id,
            });
            setVideoStatus("complete");
          }
        },
      });
    } catch (error) {
      if (controller.signal.aborted) return;
      setVideoStatus("ready");
      setVideoCaptions((current) => [
        ...current,
        {
          id: `video-error-${Date.now()}`,
          frame: current.length + 1,
          caption: error instanceof Error ? error.message : "Video analysis failed.",
          kind: "warning",
        },
      ]);
    } finally {
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null;
      }
    }
  }

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
              onStartVideo={startVideoAnalysis}
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

      <AppFooter />
    </main>
  );
}
