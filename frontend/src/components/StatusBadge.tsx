import type { ComponentType } from "react";
import { CheckCircle2, CircleDashed, Radio, TriangleAlert } from "lucide-react";

type StatusTone = "online" | "idle" | "warning" | "dark";

type StatusBadgeProps = {
  label: string;
  tone?: StatusTone;
};

const toneClass: Record<StatusTone, string> = {
  online: "border-primary bg-canvas-soft text-ink",
  idle: "border-hairline bg-canvas-soft text-ink-muted",
  warning: "border-hairline-strong bg-canvas-soft text-ink",
  dark: "border-canvas-night bg-canvas-night text-white",
};

const iconMap: Record<StatusTone, ComponentType<{ className?: string }>> = {
  online: CheckCircle2,
  idle: CircleDashed,
  warning: TriangleAlert,
  dark: Radio,
};

export function StatusBadge({ label, tone = "idle" }: StatusBadgeProps) {
  const Icon = iconMap[tone];

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 font-mono text-xs ${toneClass[tone]}`}
    >
      <Icon className="size-3.5" aria-hidden="true" />
      {label}
    </span>
  );
}
