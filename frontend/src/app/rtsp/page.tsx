"use client";

import { RtspModePage } from "@/components/RtspModePage";
import { useTheme } from "@/lib/use-theme";

export default function RtspPage() {
  const { theme, setTheme } = useTheme();
  return <RtspModePage theme={theme} onThemeChange={setTheme} />;
}
