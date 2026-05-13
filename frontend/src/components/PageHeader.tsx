"use client";

import { Moon, Sun } from "lucide-react";
import type { Theme } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";

type PageHeaderProps = {
  modeLabel: string;
  theme: Theme;
  onThemeChange: (theme: Theme) => void;
  onBack: () => void;
  controlsTrigger?: React.ReactNode;
};

export function PageHeader({
  modeLabel,
  theme,
  onThemeChange,
  onBack,
  controlsTrigger,
}: PageHeaderProps) {
  const nextTheme = theme === "light" ? "dark" : "light";

  return (
    <header className="border-b border-hairline bg-canvas">
      <div className="mx-auto flex max-w-[1440px] items-center justify-between gap-4 px-5 py-3 md:px-8">
        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={onBack}
            className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-sm text-ink-muted transition-colors duration-200 hover:bg-canvas-soft hover:text-ink focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <span aria-hidden="true">&larr;</span>
            <span className="hidden sm:inline">Change Mode</span>
          </button>

          <div className="h-5 w-px bg-hairline" />

          <div className="text-xl font-medium tracking-[-0.04em]">
            Insight<span className="text-primary-deep">Cap</span>
          </div>

          <span className="hidden font-mono text-xs uppercase tracking-wide text-ink-muted sm:inline">
            {modeLabel}
          </span>
        </div>

        <div className="flex items-center gap-3">
          <StatusBadge label="FastAPI connected" tone="online" />
          <StatusBadge label="vLLM backend" tone="idle" />

          <button
            type="button"
            aria-label={`Switch to ${nextTheme} theme`}
            onClick={() => onThemeChange(nextTheme)}
            className="inline-flex size-9 items-center justify-center rounded-md border border-hairline bg-canvas text-ink transition-colors duration-200 hover:bg-canvas-soft hover:border-hairline-strong focus:outline-none focus:ring-2 focus:ring-primary"
          >
            {theme === "light" ? (
              <Moon className="size-4" aria-hidden="true" />
            ) : (
              <Sun className="size-4" aria-hidden="true" />
            )}
          </button>

          {controlsTrigger}
        </div>
      </div>
    </header>
  );
}
