import { Camera, FileVideo2, Square, Upload } from "lucide-react";
import {
  RTSP_PROMPT_PRESETS,
  VIDEO_PROMPT_PRESETS,
} from "@/data/prompts";
import type { Mode, RtspStatus, VideoStatus } from "@/lib/types";
import { Button } from "./Button";
import { PromptEditor } from "./PromptEditor";
import { StatusBadge } from "./StatusBadge";

type ControlPanelProps = {
  mode: Mode;
  model: string;
  onModelChange: (model: string) => void;
  videoFileName: string | null;
  onVideoFileChange: (file: File | null) => void;
  videoStatus: VideoStatus;
  onStartVideo: () => void;
  videoPreset: string;
  onVideoPresetChange: (preset: string) => void;
  videoCustomPrompts: boolean;
  onVideoCustomPromptsChange: (value: boolean) => void;
  videoFramePrompt: string;
  onVideoFramePromptChange: (value: string) => void;
  videoSummaryPrompt: string;
  onVideoSummaryPromptChange: (value: string) => void;
  rtspUrl: string;
  onRtspUrlChange: (value: string) => void;
  rtspSessionName: string;
  onRtspSessionNameChange: (value: string) => void;
  sampleEverySeconds: number;
  onSampleEverySecondsChange: (value: number) => void;
  rtspStatus: RtspStatus;
  onToggleRtsp: () => void;
  rtspPreset: string;
  onRtspPresetChange: (preset: string) => void;
  rtspCustomPrompt: boolean;
  onRtspCustomPromptChange: (value: boolean) => void;
  rtspFramePrompt: string;
  onRtspFramePromptChange: (value: string) => void;
};

export function ControlPanel(props: ControlPanelProps) {
  const isVideo = props.mode === "video";
  const videoBusy =
    props.videoStatus === "initializing" || props.videoStatus === "analyzing";
  const rtspLive = props.rtspStatus === "live" || props.rtspStatus === "connecting";

  return (
    <section className="rounded-lg border border-hairline bg-canvas p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-medium tracking-[-0.03em] text-ink">
            {isVideo ? "Video controls" : "RTSP controls"}
          </h2>
          <p className="mt-1 text-sm leading-6 text-ink-muted">
            Local prototype controls mirror the current Streamlit workflow.
          </p>
        </div>
        <StatusBadge label={isVideo ? props.videoStatus : props.rtspStatus} tone={rtspLive ? "online" : "idle"} />
      </div>

      <div className="mt-5 grid gap-4">
        {isVideo ? (
          <label className="block rounded-lg border border-dashed border-hairline-strong bg-canvas-soft p-4">
            <span className="mb-3 flex items-center gap-2 font-mono text-xs uppercase tracking-wide text-ink-muted">
              <Upload className="size-4" aria-hidden="true" />
              Upload video
            </span>
            <input
              aria-label="Upload video"
              type="file"
              accept="video/mp4,video/avi,video/quicktime,video/x-matroska,video/webm,video/mpeg"
              className="block w-full text-sm text-ink file:mr-3 file:rounded-md file:border file:border-hairline-strong file:bg-canvas file:px-3 file:py-2 file:text-sm file:font-medium file:text-ink hover:file:border-ink"
              onChange={(event) => props.onVideoFileChange(event.target.files?.[0] ?? null)}
            />
            <span className="mt-2 block truncate text-sm text-ink-muted">
              {props.videoFileName ?? "Supported: MP4, AVI, MOV, MKV, WEBM, MPEG"}
            </span>
          </label>
        ) : (
          <div className="grid gap-3">
            <label className="block">
              <span className="mb-2 block font-mono text-xs uppercase tracking-wide text-ink-muted">
                RTSP URL
              </span>
              <input
                aria-label="RTSP URL"
                value={props.rtspUrl}
                onChange={(event) => props.onRtspUrlChange(event.target.value)}
                placeholder="rtsp://user:password@camera-host/stream"
                className="w-full rounded-md border border-hairline bg-canvas px-3 py-2 text-sm text-ink outline-none focus:border-primary focus:ring-2 focus:ring-primary/30"
              />
            </label>
            <label className="block">
              <span className="mb-2 block font-mono text-xs uppercase tracking-wide text-ink-muted">
                Session name
              </span>
              <input
                aria-label="Session name"
                value={props.rtspSessionName}
                onChange={(event) => props.onRtspSessionNameChange(event.target.value)}
                placeholder="front-gate"
                className="w-full rounded-md border border-hairline bg-canvas px-3 py-2 text-sm text-ink outline-none focus:border-primary focus:ring-2 focus:ring-primary/30"
              />
            </label>
            <label className="block">
              <span className="mb-2 block font-mono text-xs uppercase tracking-wide text-ink-muted">
                Sample seconds
              </span>
              <input
                aria-label="Sample seconds"
                type="number"
                min={0.2}
                max={60}
                step={0.2}
                value={props.sampleEverySeconds}
                onChange={(event) => props.onSampleEverySecondsChange(Number(event.target.value))}
                className="w-full rounded-md border border-hairline bg-canvas px-3 py-2 text-sm text-ink outline-none focus:border-primary focus:ring-2 focus:ring-primary/30"
              />
            </label>
          </div>
        )}

        <label className="block">
          <span className="mb-2 block font-mono text-xs uppercase tracking-wide text-ink-muted">
            Model
          </span>
          <select
            aria-label="Model"
            value={props.model}
            onChange={(event) => props.onModelChange(event.target.value)}
            className="w-full rounded-md border border-hairline bg-canvas px-3 py-2 text-sm text-ink outline-none focus:border-primary focus:ring-2 focus:ring-primary/30"
          >
            <option value="qwen3.5:0.8b">qwen3.5:0.8b</option>
          </select>
        </label>

        {isVideo ? (
          <VideoPromptControls {...props} />
        ) : (
          <RtspPromptControls {...props} />
        )}

        {isVideo ? (
          <Button
            variant="primary"
            onClick={props.onStartVideo}
            disabled={!props.videoFileName || videoBusy}
            icon={<FileVideo2 className="size-4" aria-hidden="true" />}
          >
            {videoBusy ? "Analyzing" : "Initiate analysis"}
          </Button>
        ) : (
          <Button
            variant={rtspLive ? "dark" : "primary"}
            onClick={props.onToggleRtsp}
            disabled={!props.rtspUrl.trim() && !rtspLive}
            icon={
              rtspLive ? (
                <Square className="size-4" aria-hidden="true" />
              ) : (
                <Camera className="size-4" aria-hidden="true" />
              )
            }
          >
            {rtspLive ? "Stop monitoring" : "Start monitoring"}
          </Button>
        )}
      </div>
    </section>
  );
}

function VideoPromptControls(props: ControlPanelProps) {
  return (
    <div className="grid gap-3 border-t border-hairline pt-4">
      <label className="block">
        <span className="mb-2 block font-mono text-xs uppercase tracking-wide text-ink-muted">
          Prompt preset
        </span>
        <select
          aria-label="Video prompt preset"
          value={props.videoPreset}
          onChange={(event) => props.onVideoPresetChange(event.target.value)}
          className="w-full rounded-md border border-hairline bg-canvas px-3 py-2 text-sm text-ink outline-none focus:border-primary focus:ring-2 focus:ring-primary/30"
        >
          {Object.keys(VIDEO_PROMPT_PRESETS).map((preset) => (
            <option key={preset} value={preset}>
              {preset}
            </option>
          ))}
        </select>
      </label>
      <label className="inline-flex items-center gap-2 text-sm text-ink">
        <input
          type="checkbox"
          checked={props.videoCustomPrompts}
          onChange={(event) => props.onVideoCustomPromptsChange(event.target.checked)}
          className="size-4 accent-primary-deep"
        />
        Custom prompts
      </label>
      <PromptEditor
        title="Frame prompt"
        value={props.videoFramePrompt}
        onChange={props.onVideoFramePromptChange}
        disabled={!props.videoCustomPrompts}
      />
      <PromptEditor
        title="Summary prompt"
        value={props.videoSummaryPrompt}
        onChange={props.onVideoSummaryPromptChange}
        disabled={!props.videoCustomPrompts}
      />
    </div>
  );
}

function RtspPromptControls(props: ControlPanelProps) {
  return (
    <div className="grid gap-3 border-t border-hairline pt-4">
      <label className="block">
        <span className="mb-2 block font-mono text-xs uppercase tracking-wide text-ink-muted">
          Prompt preset
        </span>
        <select
          aria-label="RTSP prompt preset"
          value={props.rtspPreset}
          onChange={(event) => props.onRtspPresetChange(event.target.value)}
          className="w-full rounded-md border border-hairline bg-canvas px-3 py-2 text-sm text-ink outline-none focus:border-primary focus:ring-2 focus:ring-primary/30"
        >
          {Object.keys(RTSP_PROMPT_PRESETS).map((preset) => (
            <option key={preset} value={preset}>
              {preset}
            </option>
          ))}
        </select>
      </label>
      <label className="inline-flex items-center gap-2 text-sm text-ink">
        <input
          type="checkbox"
          checked={props.rtspCustomPrompt}
          onChange={(event) => props.onRtspCustomPromptChange(event.target.checked)}
          className="size-4 accent-primary-deep"
        />
        Custom prompt
      </label>
      <PromptEditor
        title="Frame prompt"
        value={props.rtspFramePrompt}
        onChange={props.onRtspFramePromptChange}
        disabled={!props.rtspCustomPrompt}
      />
    </div>
  );
}
