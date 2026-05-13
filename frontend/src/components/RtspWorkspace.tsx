import { Camera, Radio } from "lucide-react";
import type { CaptionRow, RtspMetadata } from "@/lib/types";
import { CaptionsPanel } from "./CaptionsPanel";
import { MetadataStrip } from "./MetadataStrip";
import { StatusBadge } from "./StatusBadge";

type RtspWorkspaceProps = {
  sessionName: string;
  source: string;
  previewUrl: string | null;
  streamError: string | null;
  captions: CaptionRow[];
  metadata: RtspMetadata;
};

export function RtspWorkspace({
  sessionName,
  source,
  previewUrl,
  streamError,
  captions,
  metadata,
}: RtspWorkspaceProps) {
  const live = metadata.status === "live" || metadata.status === "connecting";

  return (
    <div className="grid gap-5">
      <section className="grid gap-5 lg:grid-cols-[1fr_1fr]">
        <section className="rounded-lg border border-hairline bg-canvas shadow-sm">
          <div className="flex items-center justify-between border-b border-hairline px-4 py-3">
            <div className="flex items-center gap-2">
              {live && (
                <span className="inline-block size-2 animate-pulse rounded-full bg-primary-deep" aria-hidden="true" />
              )}
              <h1 className="text-lg font-medium tracking-[-0.02em] text-ink">
                Live stream
              </h1>
            </div>
            <StatusBadge label={live ? "camera online" : "camera idle"} tone={live ? "online" : "idle"} />
          </div>

          <div className="p-4">
            <div className="relative overflow-hidden rounded-lg border border-hairline bg-canvas-night shadow-mockup">
              {previewUrl ? (
                // eslint-disable-next-line @next/next/no-img-element -- MJPEG streams require a plain browser image element.
                <img
                  src={previewUrl}
                  alt="RTSP live preview"
                  className="aspect-video w-full bg-canvas-night object-contain"
                />
              ) : (
                <div className="relative aspect-video bg-[linear-gradient(90deg,#1c1c1c_0,#202020_50%,#1c1c1c_100%)] p-5">
                  <div className="grid h-full grid-cols-6 gap-3 opacity-70">
                    {Array.from({ length: 18 }).map((_, index) => (
                      <div key={index} className="rounded-sm border border-white/10 bg-white/10" />
                    ))}
                  </div>
                  {streamError ? (
                    <div className="absolute inset-x-4 top-4 rounded-md border border-[#c2410c]/60 bg-[#451a03]/90 p-3 text-sm leading-6 text-white shadow-sm">
                      <div className="font-mono text-xs uppercase tracking-wide text-[#fdba74]">
                        Stream warning
                      </div>
                      <p className="mt-1 break-words">{streamError}</p>
                    </div>
                  ) : (
                    <div className="absolute inset-0 grid place-items-center px-6 text-center text-sm leading-6 text-white/70">
                      Preview will appear after the backend connects to the RTSP source.
                    </div>
                  )}
                </div>
              )}
              <div className="absolute inset-x-0 bottom-0 flex items-end justify-between gap-4 border-t border-white/10 bg-canvas-night/95 p-4 text-white">
                <div>
                  <div className="font-mono text-xs uppercase tracking-wide text-white/60">
                    {sessionName || "rtsp-camera"}
                  </div>
                  <div className="mt-1 flex items-center gap-2 text-sm">
                    <Camera className="size-4" aria-hidden="true" />
                    MJPEG preview bridge
                  </div>
                </div>
                <Radio className="size-5 text-primary" aria-hidden="true" />
              </div>
            </div>

            <div className="mt-4 rounded-lg border border-hairline bg-canvas-soft p-4">
              <div className="font-mono text-xs uppercase tracking-wide text-ink-muted">
                Source
              </div>
              <p className="mt-2 break-all text-sm leading-6 text-ink">
                {source || "Enter an RTSP URL to start backend monitoring."}
              </p>
            </div>
          </div>
        </section>

        <CaptionsPanel
          title="Live RTSP captions"
          captions={captions}
          streaming={live}
        />
      </section>

      <MetadataStrip
        items={[
          { label: "Status", value: metadata.status },
          { label: "Captions", value: metadata.captionsEmitted },
          { label: "Lag", value: metadata.lagMs === null ? "--" : `${metadata.lagMs}ms` },
          { label: "Model", value: metadata.modelId },
        ]}
      />
    </div>
  );
}
