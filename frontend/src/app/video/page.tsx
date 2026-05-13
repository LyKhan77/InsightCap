"use client";

import { VideoModePage } from "@/components/VideoModePage";
import { useTheme } from "@/lib/use-theme";

export default function VideoPage() {
  const { theme, setTheme } = useTheme();
  return <VideoModePage theme={theme} onThemeChange={setTheme} />;
}
