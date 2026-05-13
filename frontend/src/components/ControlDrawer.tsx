"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Settings, X } from "lucide-react";

type ControlDrawerProps = {
  title: string;
  children: React.ReactNode;
};

export function ControlDrawer({ title, children }: ControlDrawerProps) {
  const [open, setOpen] = useState(false);
  const drawerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  const close = useCallback(() => setOpen(false), []);

  useEffect(() => {
    if (!open) return;

    function handleKey(event: KeyboardEvent) {
      if (event.key === "Escape") close();
    }

    document.addEventListener("keydown", handleKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handleKey);
      document.body.style.overflow = "";
    };
  }, [open, close]);

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        aria-label="Open controls"
        onClick={() => setOpen(true)}
        className="inline-flex size-9 items-center justify-center rounded-md border border-hairline bg-canvas text-ink transition-colors duration-200 hover:bg-canvas-soft hover:border-hairline-strong focus:outline-none focus:ring-2 focus:ring-primary"
      >
        <Settings className="size-4" aria-hidden="true" />
      </button>

      {/* Backdrop */}
      <div
        aria-hidden="true"
        className={`fixed inset-0 z-40 bg-black/40 transition-opacity duration-300 ${
          open ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
        onClick={close}
      />

      {/* Drawer panel */}
      <div
        ref={drawerRef}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={`fixed inset-y-0 right-0 z-50 flex w-[380px] max-w-[calc(100vw-2rem)] flex-col border-l border-hairline bg-canvas shadow-mockup transition-transform duration-300 ease-out ${
          open ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between border-b border-hairline px-5 py-4">
          <h2 className="text-lg font-medium tracking-[-0.02em] text-ink">
            {title}
          </h2>
          <button
            type="button"
            aria-label="Close controls"
            onClick={close}
            className="inline-flex size-8 items-center justify-center rounded-md text-ink-muted transition-colors duration-200 hover:bg-canvas-soft hover:text-ink focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <X className="size-4" aria-hidden="true" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-5">
          {children}
        </div>
      </div>
    </>
  );
}
