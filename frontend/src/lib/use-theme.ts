"use client";

import { useEffect, useState } from "react";
import type { Theme } from "./types";

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window === "undefined") return "light";
    const saved = window.localStorage.getItem("insightcap-theme");
    return saved === "light" || saved === "dark" ? saved : "light";
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  function setTheme(next: Theme) {
    setThemeState(next);
    window.localStorage.setItem("insightcap-theme", next);
    document.documentElement.dataset.theme = next;
  }

  return { theme, setTheme };
}
