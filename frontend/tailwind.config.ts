import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/data/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "var(--canvas)",
        "canvas-soft": "var(--canvas-soft)",
        "canvas-night": "var(--canvas-night)",
        ink: "var(--ink)",
        "ink-muted": "var(--ink-muted)",
        "ink-faint": "var(--ink-faint)",
        hairline: "var(--hairline)",
        "hairline-strong": "var(--hairline-strong)",
        primary: "var(--primary)",
        "primary-deep": "var(--primary-deep)",
      },
      boxShadow: {
        mockup: "0 8px 24px rgba(0, 0, 0, 0.08)",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "ui-sans-serif", "system-ui"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "Menlo"],
      },
    },
  },
  plugins: [],
};

export default config;
