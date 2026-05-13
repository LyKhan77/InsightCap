import { Camera, FileVideo2 } from "lucide-react";
import type { Mode } from "@/lib/types";

type ModeSelectorProps = {
  onSelect: (mode: Mode) => void;
};

export function ModeSelector({ onSelect }: ModeSelectorProps) {
  return (
    <main className="mx-auto flex min-h-screen max-w-7xl flex-col px-5 py-5 md:px-8">
      <header className="flex items-center justify-between border-b border-hairline pb-5">
        <div className="text-2xl font-medium tracking-[-0.04em] text-ink">
          Insight<span className="text-primary-deep">Cap</span>
        </div>
        <span className="font-mono text-xs uppercase tracking-wide text-ink-muted">
          VLLM_BACKEND_READY
        </span>
      </header>

      <section className="grid flex-1 items-center gap-10 py-12 lg:grid-cols-[0.9fr_1.1fr]">
        <div>
          <h1 className="max-w-3xl text-5xl font-medium leading-[1.05] tracking-[-0.04em] text-ink md:text-6xl">
            Video understanding workspace for captions and live monitoring.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-ink-muted">
            Choose the same workflows from the Streamlit app, rebuilt as a
            production-grade interface with local dummy state for design validation.
          </p>
        </div>

        <div className="grid gap-4">
          <button
            type="button"
            data-testid="mode-video"
            onClick={() => onSelect("video")}
            className="group rounded-lg border border-hairline bg-canvas p-6 text-left shadow-sm transition duration-200 hover:border-ink hover:shadow-mockup focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
          >
            <div className="flex items-start justify-between gap-4">
              <FileVideo2 className="size-8 text-ink" aria-hidden="true" />
              <span className="inline-flex min-h-9 items-center justify-center rounded-md border border-primary bg-primary px-4 py-2 text-sm font-medium leading-none text-ink transition-colors duration-200 group-hover:border-primary-deep group-hover:bg-primary-deep">
                Video Analysis
              </span>
            </div>
            <h2 className="mt-8 text-3xl font-medium tracking-[-0.03em] text-ink">
              Uploaded video captions
            </h2>
            <p className="mt-3 text-sm leading-6 text-ink-muted">
              Upload a file, simulate frame captions, inspect the generated summary,
              and export the result as JSON.
            </p>
          </button>

          <button
            type="button"
            data-testid="mode-rtsp"
            onClick={() => onSelect("rtsp")}
            className="group rounded-lg border border-hairline bg-canvas p-6 text-left shadow-sm transition duration-200 hover:border-ink hover:shadow-mockup focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
          >
            <div className="flex items-start justify-between gap-4">
              <Camera className="size-8 text-ink" aria-hidden="true" />
              <span className="inline-flex min-h-9 items-center justify-center rounded-md border border-hairline-strong bg-canvas px-4 py-2 text-sm font-medium leading-none text-ink transition-colors duration-200 group-hover:border-ink group-hover:bg-canvas-soft">
                RTSP Monitoring
              </span>
            </div>
            <h2 className="mt-8 text-3xl font-medium tracking-[-0.03em] text-ink">
              Live camera session
            </h2>
            <p className="mt-3 text-sm leading-6 text-ink-muted">
              Start a dummy camera session, view a mock MJPEG bridge, and watch live
              event captions append in place.
            </p>
          </button>
        </div>
      </section>
    </main>
  );
}
