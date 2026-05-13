import Image from "next/image";

export function AppFooter() {
  return (
    <footer className="mx-auto flex w-full max-w-[1440px] items-center justify-between gap-3 px-5 pb-6 font-mono text-xs text-ink-muted md:px-8">
      <span>Develop by Lee - GSPE/</span>
      <Image
        src="/Logo-InsightCap.png"
        alt="InsightCap"
        width={96}
        height={32}
        className="h-6 w-auto opacity-80"
        priority={false}
      />
    </footer>
  );
}
