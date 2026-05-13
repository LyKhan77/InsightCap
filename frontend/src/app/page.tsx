"use client";

import { useState } from "react";
import { ModeSwitchPage } from "@/components/ModeSwitchPage";
import { useTheme } from "@/lib/use-theme";

export default function Home() {
  const { theme, setTheme } = useTheme();
  return <ModeSwitchPage theme={theme} onThemeChange={setTheme} />;
}
