import { forwardRef } from "react";
import { Download, Play } from "lucide-react";
import type { CaptionRow, VideoMetadata, VideoStatus } from "@/lib/types";
import { buildAnalysisExport, downloadJson } from "@/lib/export";
import { Button } from "./Button";
import { CaptionsPanel } from "./CaptionsPanel";
import { MetadataStrip } from "./MetadataStrip";

type DisplayPhase = "idle" | "ready" | "uploading" | "analyzing" | "summarizing" | "complete";

type VideoWorkspaceProps = {
  fileName: string | null;
  fileUrl: string | null;
  status: VideoStatus;
  captions: CaptionRow[];
  finalCaption: string | null;
  metadata: VideoMetadata;
  videoCurrentTime: number;
  backendFinished: boolean;
  videoPlaying: boolean;
  videoEnded: boolean;
};

export const VideoWorkspace = forwardRef<HTMLVideoElement, VideoWorkspaceProps>(function VideoWorkspace({
  fileName,
  fileUrl,
  status,
  captions,
  finalCaption,
  metadata,
  videoCurrentTime,
  backendFinished,
  videoPlaying,
  videoEnded,
}: VideoWorkspaceProps, videoRef) {
  const visibleCaptions = videoEnded
    ? captions
    : captions.filter((c) => {
        if (c.timestampEnd == null) return true;
        return c.timestampEnd <= videoCurrentTime + 1;
      });

  const allRevealed = visibleCaptions.length === captions.length && captions.length > 0;

  const phase: DisplayPhase = (() => {
    if (status === "idle") return "idle";
    if (status === "ready") return "ready";
    if (status === "initializing") return "uploading";
    if (allRevealed && finalCaption) return "complete";
    if (allRevealed && backendFinished) return "summarizing";
    return "analyzing";
  })();

  const isStreaming = phase === "analyzing" || phase === "uploading" || phase === "summarizing";

  const pipelineText: Record<DisplayPhase, string> = {
    idle: "Waiting for a file.",
    ready: "Ready to run backend analysis.",
    uploading: "Uploading video and reading metadata...",
    analyzing: `Streaming segment captions... (${visibleCaptions.length}/${captions.length} revealed)`,
    summarizing: "Generating summary...",
    complete: "Analysis complete. Summary and export available.",
  };

  const showExport = phase === "complete";
  const showFinalCaption = phase === "complete";

  return (
    <div className="grid gap-5">
      <section className="grid gap-5 lg:grid-cols-[1fr_1fr]">
        <section className="rounded-lg border border-hairline bg-canvas shadow-sm">
          <div className="flex items-center justify-between border-b border-hairline px-4 py-3">
            <div className="flex items-center gap-2">
              {isStreaming && (
                <span className="inline-block size-2 animate-pulse rounded-full bg-primary-deep" aria-hidden="true" />
              )}
              <h1 className="text-lg font-medium tracking-[-0.02em] text-ink">
                Live stream
              </h1>
            </div>
            <span className="font-mono text-xs uppercase tracking-wide text-ink-muted">
              {fileName ?? "No file"}
            </span>
          </div>

          <div className="p-4">
            {fileUrl ? (
              <div className="overflow-hidden rounded-lg border border-hairline bg-canvas-night shadow-mockup">
                <video
                  ref={videoRef}
                  src={fileUrl}
                  controls={status === "initializing" || (status === "analyzing" && !backendFinished)}
                  playsInline
                  preload="auto"
                  className="aspect-video w-full bg-canvas-night object-contain"
                />
              </div>
            ) : (
              <div className="grid aspect-video place-items-center rounded-lg border border-dashed border-hairline bg-canvas-soft">
                <div className="text-center">
                  <Play className="mx-auto size-9 text-ink-muted" aria-hidden="true" />
                  <p className="mt-3 text-sm text-ink-muted">Upload a video to begin.</p>
                </div>
              </div>
            )}

            <div className="mt-4 rounded-lg border border-hairline bg-canvas-soft p-4">
              <div className="font-mono text-xs uppercase tracking-wide text-ink-muted">
                Pipeline state
              </div>
              <div className="mt-2 flex items-center justify-between gap-4">
                <p className="text-sm leading-6 text-ink">
                  {pipelineText[phase]}
                </p>
                {showExport && finalCaption ? (
                  <Button
                    variant="secondary"
                    icon={<Download className="size-4" aria-hidden="true" />}
                    onClick={() =>
                      downloadJson(
                        `analysis_${metadata.frameCount}.json`,
                        buildAnalysisExport(finalCaption, captions, metadata),
                      )
                    }
                  >
                    JSON
                  </Button>
                ) : null}
              </div>
            </div>
          </div>
        </section>

        <CaptionsPanel
          captions={visibleCaptions}
          streaming={phase === "analyzing" || phase === "uploading" || phase === "summarizing"}
          finalCaption={showFinalCaption ? (finalCaption ?? undefined) : undefined}
        />
      </section>

      <MetadataStrip
        items={[
          { label: "Frames", value: metadata.frameCount },
          { label: "Duration", value: `${metadata.durationSeconds.toFixed(1)}s` },
          { label: "Device", value: metadata.deviceUsed },
          { label: "Model", value: metadata.modelId },
        ]}
      />
    </div>
  );
});
