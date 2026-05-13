"use client";

import { ArrowDownToLine } from "lucide-react";
import { useEffect, useRef, useState } from "react";
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
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [stickToLatest, setStickToLatest] = useState(true);

  useEffect(() => {
    if (!stickToLatest) return;
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [captions.length, finalCaption, stickToLatest]);

  function handleScroll() {
    const el = scrollRef.current;
    if (!el) return;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    setStickToLatest(distanceFromBottom < 48);
  }

  function scrollToLatest() {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    setStickToLatest(true);
  }

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

      <div className="relative">
        <div
          ref={scrollRef}
          onScroll={handleScroll}
          className="flex-1 overflow-y-auto px-4 py-3"
          style={{ maxHeight: "calc(100vh - 340px)", minHeight: "320px" }}
        >
        {captions.length === 0 ? (
          <div className="flex min-h-[240px] items-center justify-center rounded-md border border-dashed border-hairline bg-canvas-soft text-center text-sm leading-6 text-ink-muted">
            Captions will appear here when the backend stream starts.
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

        {!stickToLatest && captions.length > 0 ? (
          <button
            type="button"
            onClick={scrollToLatest}
            className="absolute bottom-4 right-4 inline-flex items-center gap-2 rounded-md border border-primary-deep bg-canvas px-3 py-2 text-xs font-medium text-primary-deep shadow-sm transition-colors duration-200 hover:bg-primary hover:text-on-primary focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <ArrowDownToLine className="size-4" aria-hidden="true" />
            Latest frame
          </button>
        ) : null}
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
