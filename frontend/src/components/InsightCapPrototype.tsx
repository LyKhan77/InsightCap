"use client";

import { useEffect, useMemo, useState } from "react";
import {
  RTSP_PROMPT_PRESETS,
  VIDEO_PROMPT_PRESETS,
} from "@/data/prompts";
import {
  DUMMY_SUMMARY,
  RTSP_SAMPLE_CAPTIONS,
  VIDEO_SAMPLE_CAPTIONS,
} from "@/lib/dummy-data";
import type {
  CaptionRow,
  Mode,
  RtspMetadata,
  RtspStatus,
  VideoMetadata,
  VideoStatus,
} from "@/lib/types";
import { AppShell } from "./AppShell";
import { ControlPanel } from "./ControlPanel";
import { ModeSelector } from "./ModeSelector";
import { RtspWorkspace } from "./RtspWorkspace";
import { VideoWorkspace } from "./VideoWorkspace";

const DEFAULT_MODEL = "qwen3.5:0.8b";

export function InsightCapPrototype() {
  const [mode, setMode] = useState<Mode | null>(null);
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

  const fileUrl = useMemo(() => {
    if (!videoFile) {
      return null;
    }
    return URL.createObjectURL(videoFile);
  }, [videoFile]);

  useEffect(() => {
    return () => {
      if (fileUrl) {
        URL.revokeObjectURL(fileUrl);
      }
    };
  }, [fileUrl]);

  useEffect(() => {
    if (rtspStatus !== "live") {
      return;
    }

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

  function handleVideoFileChange(file: File | null) {
    setVideoFile(file);
    setVideoStatus(file ? "ready" : "idle");
    setVideoCaptions([]);
    setFinalCaption(null);
  }

  function handleVideoPresetChange(presetName: string) {
    setVideoPreset(presetName);
    if (!videoCustomPrompts) {
      const preset = VIDEO_PROMPT_PRESETS[presetName];
      setVideoFramePrompt(preset.framePrompt);
      setVideoSummaryPrompt(preset.summaryPrompt);
    }
  }

  function handleVideoCustomPromptsChange(enabled: boolean) {
    setVideoCustomPrompts(enabled);
    if (!enabled) {
      const preset = VIDEO_PROMPT_PRESETS[videoPreset];
      setVideoFramePrompt(preset.framePrompt);
      setVideoSummaryPrompt(preset.summaryPrompt);
    }
  }

  function handleRtspPresetChange(presetName: string) {
    setRtspPreset(presetName);
    if (!rtspCustomPrompt) {
      setRtspFramePrompt(RTSP_PROMPT_PRESETS[presetName].framePrompt);
    }
  }

  function handleRtspCustomPromptChange(enabled: boolean) {
    setRtspCustomPrompt(enabled);
    if (!enabled) {
      setRtspFramePrompt(RTSP_PROMPT_PRESETS[rtspPreset].framePrompt);
    }
  }

  function startVideoSimulation() {
    if (!videoFile || videoStatus === "analyzing") {
      return;
    }

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

  function toggleRtspSimulation() {
    if (rtspStatus === "live" || rtspStatus === "connecting") {
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

  const videoMetadata: VideoMetadata = {
    frameCount: videoStatus === "complete" ? videoCaptions.length : videoCaptions.length,
    durationSeconds: videoFile ? 4.8 : 0,
    deviceUsed: "dummy",
    modelId: model,
  };

  const rtspMetadata: RtspMetadata = {
    status: rtspStatus,
    captionsEmitted: rtspCaptions.filter((caption) => caption.kind !== "system").length,
    lagMs: rtspStatus === "live" ? 132 : null,
    modelId: model,
    reconnectCount: 0,
  };

  if (!mode) {
    return <ModeSelector onSelect={setMode} />;
  }

  return (
    <AppShell
      mode={mode}
      onModeChange={setMode}
      controlPanel={
        <ControlPanel
          mode={mode}
          model={model}
          onModelChange={setModel}
          videoFileName={videoFile?.name ?? null}
          onVideoFileChange={handleVideoFileChange}
          videoStatus={videoStatus}
          onStartVideo={startVideoSimulation}
          videoPreset={videoPreset}
          onVideoPresetChange={handleVideoPresetChange}
          videoCustomPrompts={videoCustomPrompts}
          onVideoCustomPromptsChange={handleVideoCustomPromptsChange}
          videoFramePrompt={videoFramePrompt}
          onVideoFramePromptChange={setVideoFramePrompt}
          videoSummaryPrompt={videoSummaryPrompt}
          onVideoSummaryPromptChange={setVideoSummaryPrompt}
          rtspUrl={rtspUrl}
          onRtspUrlChange={setRtspUrl}
          rtspSessionName={rtspSessionName}
          onRtspSessionNameChange={setRtspSessionName}
          sampleEverySeconds={sampleEverySeconds}
          onSampleEverySecondsChange={setSampleEverySeconds}
          rtspStatus={rtspStatus}
          onToggleRtsp={toggleRtspSimulation}
          rtspPreset={rtspPreset}
          onRtspPresetChange={handleRtspPresetChange}
          rtspCustomPrompt={rtspCustomPrompt}
          onRtspCustomPromptChange={handleRtspCustomPromptChange}
          rtspFramePrompt={rtspFramePrompt}
          onRtspFramePromptChange={setRtspFramePrompt}
        />
      }
      workspace={
        mode === "video" ? (
          <VideoWorkspace
            fileName={videoFile?.name ?? null}
            fileUrl={fileUrl}
            status={videoStatus}
            captions={videoCaptions}
            finalCaption={finalCaption}
            metadata={videoMetadata}
          />
        ) : (
          <RtspWorkspace
            sessionName={rtspSessionName}
            source={rtspUrl}
            captions={rtspCaptions}
            metadata={rtspMetadata}
          />
        )
      }
    />
  );
}
