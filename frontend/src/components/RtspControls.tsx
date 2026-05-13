import { Camera, Square } from "lucide-react";
import { RTSP_PROMPT_PRESETS } from "@/data/prompts";
import type { RtspStatus } from "@/lib/types";
import { Button } from "./Button";
import { PromptEditor } from "./PromptEditor";

type RtspControlsProps = {
  model: string;
  onModelChange: (model: string) => void;
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

export function RtspControls(props: RtspControlsProps) {
  const rtspLive = props.rtspStatus === "live" || props.rtspStatus === "connecting";

  return (
    <div className="grid gap-5">
      {/* Connection */}
      <div className="grid gap-3">
        <label className="block">
          <span className="mb-2 block font-mono text-xs uppercase tracking-wide text-ink-muted">
            RTSP URL
          </span>
          <input
            aria-label="RTSP URL"
            value={props.rtspUrl}
            onChange={(event) => props.onRtspUrlChange(event.target.value)}
            placeholder="rtsp://.../stream"
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

        <label className="mt-3 inline-flex items-center gap-2 text-sm text-ink">
          <input
            type="checkbox"
            checked={props.rtspCustomPrompt}
            onChange={(event) => props.onRtspCustomPromptChange(event.target.checked)}
            className="size-4 accent-primary-deep"
          />
          Custom prompt
        </label>
      </div>

      {/* Custom prompt */}
      {props.rtspCustomPrompt && (
        <PromptEditor
          title="Frame prompt"
          value={props.rtspFramePrompt}
          onChange={props.onRtspFramePromptChange}
        />
      )}

      {/* Action */}
      <div className="border-t border-hairline pt-4">
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
          className="w-full"
        >
          {rtspLive ? "Stop monitoring" : "Start monitoring"}
        </Button>
      </div>
    </div>
  );
}
