type PromptEditorProps = {
  title: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
  rows?: number;
};

export function PromptEditor({
  title,
  value,
  onChange,
  disabled = false,
  placeholder,
  rows = 5,
}: PromptEditorProps) {
  const id = title.toLowerCase().replace(/[^a-z0-9]+/g, "-");

  return (
    <label className="block">
      <span className="mb-2 block font-mono text-xs uppercase tracking-wide text-ink-muted">
        {title}
      </span>
      <textarea
        id={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
        placeholder={placeholder}
        rows={rows}
        className="w-full resize-y rounded-md border border-hairline bg-canvas px-3 py-2 text-sm leading-6 text-ink outline-none transition-colors duration-200 placeholder:text-ink-faint focus:border-primary focus:ring-2 focus:ring-primary/30 disabled:bg-canvas-soft"
      />
    </label>
  );
}
