import { Database, Timer } from "lucide-react";
import { autoLabelOverlayUrl } from "@/lib/api";
import type { AutoLabelStatus } from "@/lib/types";

type AutoLabelPanelProps = {
  status: AutoLabelStatus;
};

export function AutoLabelPanel({ status }: AutoLabelPanelProps) {
  const active = status.status === "active" || status.status === "draining";
  const remaining =
    status.remainingSeconds === null ? "--" : `${Math.ceil(status.remainingSeconds)}s`;

  return (
    <section className="rounded-lg border border-hairline bg-canvas shadow-sm">
      <div className="flex items-center justify-between border-b border-hairline px-4 py-3">
        <div className="flex items-center gap-2">
          {active ? (
            <span className="inline-block size-2 animate-pulse rounded-full bg-primary-deep" aria-hidden="true" />
          ) : null}
          <h2 className="text-base font-medium text-ink">Auto-Labelling</h2>
        </div>
        <span className="font-mono text-xs uppercase tracking-wide text-ink-muted">
          {status.status}
        </span>
      </div>

      <div className="grid gap-4 p-4 md:grid-cols-[minmax(0,1fr)_220px]">
        <div className="grid gap-3">
          <div className="grid grid-cols-3 gap-3">
            <Metric label="Labelled" value={status.framesLabelled} />
            <Metric label="Dropped" value={status.framesDropped} />
            <Metric label="Remaining" value={remaining} />
          </div>

          <div className="rounded-md border border-hairline bg-canvas-soft p-3">
            <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-wide text-ink-muted">
              <Database className="size-3.5" aria-hidden="true" />
              Dataset
            </div>
            <p className="mt-2 break-all text-sm leading-6 text-ink">
              {status.datasetPath ?? "No dataset has been created yet."}
            </p>
          </div>

          {status.lastError ? (
            <div className="rounded-md border border-[#c2410c]/60 bg-[#451a03]/90 p-3 text-sm text-white">
              {status.lastError}
            </div>
          ) : null}
        </div>

        <div className="grid min-h-[140px] place-items-center rounded-md border border-hairline bg-canvas-soft p-3">
          {status.latestOverlayPath ? (
            <div className="w-full">
              {/* eslint-disable-next-line @next/next/no-img-element -- backend serves generated dataset previews by path. */}
              <img
                src={autoLabelOverlayUrl(status.latestOverlayPath)}
                alt="Latest annotated auto-label frame"
                className="aspect-video w-full rounded border border-hairline bg-canvas-night object-contain"
              />
              <p className="mt-2 break-all text-xs leading-5 text-ink-muted">
                {status.latestOverlayPath}
              </p>
            </div>
          ) : (
            <div className="text-center text-sm text-ink-muted">
              <Timer className="mx-auto size-7" aria-hidden="true" />
              <p className="mt-2">Latest annotated frame appears after the first labelled frame.</p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-hairline bg-canvas-soft p-3">
      <div className="font-mono text-xs uppercase tracking-wide text-ink-muted">
        {label}
      </div>
      <div className="mt-1 text-lg font-medium text-ink">{value}</div>
    </div>
  );
}
