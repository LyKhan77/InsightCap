import { FileVideo2, Upload } from "lucide-react";
import { VIDEO_PROMPT_PRESETS } from "@/data/prompts";
import type { VideoStatus } from "@/lib/types";
import { Button } from "./Button";
import { PromptEditor } from "./PromptEditor";

type VideoControlsProps = {
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
};

export function VideoControls(props: VideoControlsProps) {
  const videoBusy =
    props.videoStatus === "initializing" || props.videoStatus === "analyzing";

  return (
    <div className="grid gap-5">
      {/* Upload */}
      <div>
        <span className="mb-2 block font-mono text-xs uppercase tracking-wide text-ink-muted">
          Upload video
        </span>
        <label className="block rounded-lg border border-dashed border-hairline-strong bg-canvas-soft p-4 transition-colors duration-200 hover:border-primary-deep">
          <span className="mb-2 flex items-center gap-2 text-sm text-ink-muted">
            <Upload className="size-4" aria-hidden="true" />
            Choose file
          </span>
          <input
            aria-label="Upload video"
            type="file"
            accept="video/mp4,video/avi,video/quicktime,video/x-matroska,video/webm,video/mpeg"
            className="block w-full text-sm text-ink file:mr-3 file:rounded-md file:border file:border-hairline-strong file:bg-canvas file:px-3 file:py-2 file:text-sm file:font-medium file:text-ink hover:file:border-ink"
            onChange={(event) => props.onVideoFileChange(event.target.files?.[0] ?? null)}
          />
          <span className="mt-2 block truncate text-xs text-ink-muted">
            {props.videoFileName ?? "MP4, AVI, MOV, MKV, WEBM, MPEG"}
          </span>
        </label>
      </div>

      {/* Model */}
      <div>
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
      </div>

      {/* Prompt preset */}
      <div className="border-t border-hairline pt-4">
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

        <label className="mt-3 inline-flex items-center gap-2 text-sm text-ink">
          <input
            type="checkbox"
            checked={props.videoCustomPrompts}
            onChange={(event) => props.onVideoCustomPromptsChange(event.target.checked)}
            className="size-4 accent-primary-deep"
          />
          Custom prompts
        </label>
      </div>

      {/* Custom prompts */}
      {props.videoCustomPrompts && (
        <div className="grid gap-3">
          <PromptEditor
            title="Frame prompt"
            value={props.videoFramePrompt}
            onChange={props.onVideoFramePromptChange}
          />
          <PromptEditor
            title="Summary prompt"
            value={props.videoSummaryPrompt}
            onChange={props.onVideoSummaryPromptChange}
          />
        </div>
      )}

      {/* Action */}
      <div className="border-t border-hairline pt-4">
        <Button
          variant="primary"
          onClick={props.onStartVideo}
          disabled={!props.videoFileName || videoBusy}
          icon={<FileVideo2 className="size-4" aria-hidden="true" />}
          className="w-full"
        >
          {videoBusy ? "Analyzing..." : "Initiate analysis"}
        </Button>
      </div>
    </div>
  );
}
