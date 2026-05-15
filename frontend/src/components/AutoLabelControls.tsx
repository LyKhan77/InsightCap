import { Tag } from "lucide-react";
import type { AutoLabelConfig, AutoLabelStatus } from "@/lib/types";
import { Button } from "./Button";
import { PromptEditor } from "./PromptEditor";

type AutoLabelControlsProps = {
  config: AutoLabelConfig;
  onConfigChange: (config: AutoLabelConfig) => void;
  status?: AutoLabelStatus;
  disabled?: boolean;
  actionLabel?: string;
  onAction?: () => void;
};

export function AutoLabelControls({
  config,
  onConfigChange,
  status,
  disabled = false,
  actionLabel,
  onAction,
}: AutoLabelControlsProps) {
  const active = status?.status === "active" || status?.status === "draining";

  return (
    <div className="border-t border-hairline pt-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <div className="font-mono text-xs uppercase tracking-wide text-ink-muted">
            Auto-Labelling
          </div>
          <p className="mt-1 text-xs leading-5 text-ink-muted">
            Draft YOLO dataset from caption chunks.
          </p>
        </div>
        <label className="inline-flex items-center gap-2 text-sm text-ink">
          <input
            type="checkbox"
            checked={config.enabled}
            onChange={(event) => onConfigChange({ ...config, enabled: event.target.checked })}
            className="size-4 accent-primary-deep"
          />
          Enable
        </label>
      </div>

      {config.enabled ? (
        <div className="grid gap-3">
          <PromptEditor
            title="Label prompt"
            value={config.prompt}
            onChange={(prompt) => onConfigChange({ ...config, prompt })}
          />

          <div className="grid grid-cols-2 gap-3">
            <label className="block">
              <span className="mb-2 block font-mono text-xs uppercase tracking-wide text-ink-muted">
                Duration min
              </span>
              <input
                aria-label="Auto-label duration minutes"
                type="number"
                min={0.1}
                max={1440}
                step={0.5}
                value={config.durationMinutes}
                onChange={(event) => onConfigChange({ ...config, durationMinutes: Number(event.target.value) })}
                className="w-full rounded-md border border-hairline bg-canvas px-3 py-2 text-sm text-ink outline-none focus:border-primary focus:ring-2 focus:ring-primary/30"
              />
            </label>
            <label className="block">
              <span className="mb-2 block font-mono text-xs uppercase tracking-wide text-ink-muted">
                Confidence
              </span>
              <input
                aria-label="Auto-label confidence"
                type="number"
                min={0}
                max={1}
                step={0.05}
                value={config.confidence}
                onChange={(event) => onConfigChange({ ...config, confidence: Number(event.target.value) })}
                className="w-full rounded-md border border-hairline bg-canvas px-3 py-2 text-sm text-ink outline-none focus:border-primary focus:ring-2 focus:ring-primary/30"
              />
            </label>
          </div>

          <label className="block">
            <span className="mb-2 block font-mono text-xs uppercase tracking-wide text-ink-muted">
              Detector model
            </span>
            <select
              aria-label="Auto-label detector model"
              value={config.model}
              onChange={(event) => onConfigChange({ ...config, model: event.target.value })}
              className="w-full rounded-md border border-hairline bg-canvas px-3 py-2 text-sm text-ink outline-none focus:border-primary focus:ring-2 focus:ring-primary/30"
            >
              <option value="yolov8s-worldv2.pt">yolov8s-worldv2.pt</option>
              <option value="yolov8m-worldv2.pt">yolov8m-worldv2.pt</option>
            </select>
          </label>

          {onAction ? (
            <Button
              variant={active ? "dark" : "secondary"}
              onClick={onAction}
              disabled={disabled || !config.prompt.trim()}
              icon={<Tag className="size-4" aria-hidden="true" />}
              className="w-full"
            >
              {actionLabel ?? (active ? "Stop Auto-Labelling" : "Start Auto-Labelling")}
            </Button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
