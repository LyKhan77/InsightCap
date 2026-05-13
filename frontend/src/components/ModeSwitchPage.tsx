"use client";

import { Camera, FileVideo2, Moon, Sun } from "lucide-react";
import { useRouter } from "next/navigation";
import type { Theme } from "@/lib/types";

type ModeSwitchPageProps = {
  theme: Theme;
  onThemeChange: (theme: Theme) => void;
};

export function ModeSwitchPage({ theme, onThemeChange }: ModeSwitchPageProps) {
  const router = useRouter();
  const nextTheme = theme === "light" ? "dark" : "light";

  return (
    <main data-theme={theme} className="min-h-screen bg-canvas text-ink">
      {/* Header */}
      <header className="border-b border-hairline bg-canvas">
        <div className="mx-auto flex max-w-[1440px] items-center justify-between px-5 py-4 md:px-8">
          <div className="text-2xl font-medium tracking-[-0.04em]">
            Insight<span className="text-primary-deep">Cap</span>
          </div>
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
        </div>
      </header>

      {/* Hero */}
      <section className="mx-auto max-w-[1440px] px-5 pt-16 pb-12 md:px-8 md:pt-24 md:pb-16">
        <div className="text-center">
          <h1 className="text-5xl font-medium tracking-[-0.04em] md:text-6xl md:tracking-[-0.06em]">
            Insight<span className="text-primary-deep">Cap</span>
          </h1>
          <p className="mx-auto mt-4 max-w-md text-lg leading-7 text-ink-muted">
            Dashboard Live Captioning System
          </p>
          <p className="mx-auto mt-3 max-w-sm text-sm leading-6 text-ink-muted">
            Select a monitoring mode to begin.
          </p>
        </div>
      </section>

      {/* Mode Cards */}
      <section className="mx-auto max-w-[1440px] px-5 pb-20 md:px-8 md:pb-28">
        <div className="mx-auto grid max-w-2xl gap-6 md:grid-cols-2">
          {/* Video Card */}
          <button
            type="button"
            onClick={() => router.push("/video")}
            className="group rounded-lg border border-hairline bg-canvas p-8 text-left transition-all duration-200 hover:border-primary-deep hover:shadow-mockup focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <div className="mb-4 inline-flex size-12 items-center justify-center rounded-lg border border-hairline bg-canvas-soft text-ink-muted transition-colors duration-200 group-hover:border-primary-deep group-hover:text-primary-deep">
              <FileVideo2 className="size-6" aria-hidden="true" />
            </div>
            <h2 className="text-xl font-medium tracking-[-0.02em] text-ink">
              Video
            </h2>
            <p className="mt-3 text-sm leading-6 text-ink-muted">
              Upload a local clip, run batch analysis, and review frame captions with a final summary.
            </p>
            <span className="mt-6 inline-flex items-center gap-1.5 text-sm font-medium text-primary-deep transition-transform duration-200 group-hover:translate-x-0.5">
              Enter Video
              <span aria-hidden="true">&rarr;</span>
            </span>
          </button>

          {/* RTSP Card */}
          <button
            type="button"
            onClick={() => router.push("/rtsp")}
            className="group rounded-lg border border-hairline bg-canvas p-8 text-left transition-all duration-200 hover:border-primary-deep hover:shadow-mockup focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <div className="mb-4 inline-flex size-12 items-center justify-center rounded-lg border border-hairline bg-canvas-soft text-ink-muted transition-colors duration-200 group-hover:border-primary-deep group-hover:text-primary-deep">
              <Camera className="size-6" aria-hidden="true" />
            </div>
            <h2 className="text-xl font-medium tracking-[-0.02em] text-ink">
              RTSP
            </h2>
            <p className="mt-3 text-sm leading-6 text-ink-muted">
              Monitor a live camera source through RTSP with real-time caption streaming.
            </p>
            <span className="mt-6 inline-flex items-center gap-1.5 text-sm font-medium text-primary-deep transition-transform duration-200 group-hover:translate-x-0.5">
              Enter RTSP
              <span aria-hidden="true">&rarr;</span>
            </span>
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="mx-auto max-w-[1440px] px-5 pb-8 font-mono text-xs text-ink-muted md:px-8">
        FastAPI backend integration active.
      </footer>
    </main>
  );
}
