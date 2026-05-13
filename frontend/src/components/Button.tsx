import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "dark";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  icon?: ReactNode;
};

const variants: Record<ButtonVariant, string> = {
  primary:
    "border-primary bg-primary text-ink hover:bg-primary-deep hover:border-primary-deep",
  secondary:
    "border-hairline-strong bg-canvas text-ink hover:border-ink hover:bg-canvas-soft",
  ghost:
    "border-transparent bg-transparent text-ink hover:bg-canvas-soft hover:border-hairline",
  dark:
    "border-canvas-night bg-canvas-night text-white hover:bg-[#2a2a2a] hover:border-[#2a2a2a]",
};

export function Button({
  children,
  className = "",
  icon,
  type = "button",
  variant = "secondary",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={`inline-flex min-h-9 items-center justify-center gap-2 rounded-md border px-4 py-2 text-sm font-medium leading-none transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50 ${variants[variant]} ${className}`}
      {...props}
    >
      {icon ? <span className="grid size-4 place-items-center">{icon}</span> : null}
      <span>{children}</span>
    </button>
  );
}
