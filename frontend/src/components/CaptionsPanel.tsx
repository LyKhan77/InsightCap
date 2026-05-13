import type { CaptionRow } from "@/lib/types";

type CaptionsPanelProps = {
  title?: string;
  captions: CaptionRow[];
  streaming?: boolean;
  finalCaption?: string;
};

export function CaptionsPanel({
  title = "Live captions",
  captions,
  streaming = false,
  finalCaption,
}: CaptionsPanelProps) {
  return (
    <section className="flex flex-col rounded-lg border border-hairline bg-canvas shadow-sm">
      <div className="flex items-center justify-between border-b border-hairline px-4 py-3">
        <div className="flex items-center gap-2">
          {streaming && (
            <span className="inline-block size-2 animate-pulse rounded-full bg-primary-deep" aria-hidden="true" />
          )}
          <h2 className="text-lg font-medium tracking-[-0.02em] text-ink">{title}</h2>
        </div>
        <span className="font-mono text-xs uppercase tracking-wide text-ink-muted">
          {streaming ? "Streaming" : `${captions.length} rows`}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3" style={{ maxHeight: "calc(100vh - 340px)", minHeight: "320px" }}>
        {captions.length === 0 ? (
          <div className="flex min-h-[240px] items-center justify-center rounded-md border border-dashed border-hairline bg-canvas-soft text-center text-sm leading-6 text-ink-muted">
            Captions will appear here when the local simulation starts.
          </div>
        ) : (
          <div className="grid gap-2">
            {captions.map((row, index) => (
              <article
                key={`${row.id}-${index}`}
                className={`border-l-2 bg-canvas-soft px-3 py-2 ${
                  row.kind === "warning"
                    ? "border-[#c2410c]"
                    : row.kind === "system"
                      ? "border-hairline-strong"
                      : "border-primary-deep"
                }`}
              >
                <div className="flex items-start gap-3">
                  <span className="min-w-10 font-mono text-xs font-medium uppercase text-ink-muted">
                    F{String(row.frame).padStart(2, "0")}
                  </span>
                  <div>
                    <p className="text-sm leading-6 text-ink">{row.caption}</p>
                    {row.meta ? (
                      <p className="mt-1 font-mono text-[11px] uppercase tracking-wide text-ink-muted">
                        {row.meta}
                      </p>
                    ) : null}
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>

      {streaming ? (
        <div className="border-t border-hairline px-4 py-3 font-mono text-xs uppercase tracking-wide text-ink-muted">
          Processing next frame...
        </div>
      ) : null}

      {finalCaption ? (
        <div className="border-t border-hairline p-4">
          <div className="mb-2 font-mono text-xs uppercase tracking-wide text-primary-deep">
            Final caption
          </div>
          <p className="rounded-md border border-hairline bg-canvas-soft p-3 text-sm leading-6 text-ink">
            {finalCaption}
          </p>
        </div>
      ) : null}
    </section>
  );
}
