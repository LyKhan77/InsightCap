import { Activity, RotateCcw } from "lucide-react";
import type { Mode } from "@/lib/types";
import { Button } from "./Button";
import { StatusBadge } from "./StatusBadge";

type AppShellProps = {
  mode: Mode;
  controlPanel: React.ReactNode;
  workspace: React.ReactNode;
  onModeChange: (mode: Mode | null) => void;
};

export function AppShell({
  mode,
  controlPanel,
  workspace,
  onModeChange,
}: AppShellProps) {
  return (
    <main className="min-h-screen bg-canvas text-ink">
      <header className="border-b border-hairline bg-canvas">
        <div className="mx-auto flex max-w-[1440px] flex-wrap items-center justify-between gap-4 px-5 py-4 md:px-8">
          <div>
            <div className="text-2xl font-medium tracking-[-0.04em]">
              Insight<span className="text-primary-deep">Cap</span>
            </div>
            <div className="mt-1 font-mono text-xs uppercase tracking-wide text-ink-muted">
              {mode === "video" ? "Video Captioning System" : "RTSP Monitoring System"}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge label="API dummy mode" tone="warning" />
            <StatusBadge label="vLLM backend reserved" tone="idle" />
            <Button
              variant="ghost"
              icon={<RotateCcw className="size-4" aria-hidden="true" />}
              onClick={() => onModeChange(null)}
            >
              Select mode
            </Button>
          </div>
        </div>
      </header>

      <section className="mx-auto grid max-w-[1440px] gap-6 px-5 py-6 md:px-8 xl:grid-cols-[360px_1fr]">
        <aside className="xl:sticky xl:top-6 xl:self-start">{controlPanel}</aside>
        <section className="grid gap-5">{workspace}</section>
      </section>

      <footer className="mx-auto flex max-w-[1440px] items-center gap-2 px-5 pb-8 font-mono text-xs text-ink-muted md:px-8">
        <Activity className="size-4" aria-hidden="true" />
        Frontend prototype only. Backend integration is intentionally disabled in this phase.
      </footer>
    </main>
  );
}
