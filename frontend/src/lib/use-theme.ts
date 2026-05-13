"use client";

import { useEffect, useState } from "react";
import type { Theme } from "./types";

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>("light");

  useEffect(() => {
    const saved = window.localStorage.getItem("insightcap-theme");
    if (saved === "light" || saved === "dark") {
      setThemeState(saved);
      document.documentElement.dataset.theme = saved;
    }
  }, []);

  function setTheme(next: Theme) {
    setThemeState(next);
    window.localStorage.setItem("insightcap-theme", next);
    document.documentElement.dataset.theme = next;
  }

  return { theme, setTheme };
}
