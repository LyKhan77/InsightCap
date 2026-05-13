type MetadataItem = {
  label: string;
  value: string | number;
};

type MetadataStripProps = {
  items: MetadataItem[];
};

export function MetadataStrip({ items }: MetadataStripProps) {
  return (
    <section
      aria-label="Metadata"
      className="grid gap-px overflow-hidden rounded-lg border border-hairline bg-hairline md:grid-cols-4"
    >
      {items.map((item) => (
        <div key={item.label} className="bg-canvas px-4 py-3">
          <div className="font-mono text-[11px] uppercase tracking-wide text-ink-muted">
            {item.label}
          </div>
          <div className="mt-1 truncate text-base font-medium text-ink">{item.value}</div>
        </div>
      ))}
    </section>
  );
}
