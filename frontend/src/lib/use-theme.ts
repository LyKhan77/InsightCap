"use client";

import { useSyncExternalStore } from "react";
import type { Theme } from "./types";

const THEME_STORAGE_KEY = "insightcap-theme";
const THEME_CHANGE_EVENT = "insightcap-theme-change";

export function useTheme() {
  const theme = useSyncExternalStore(subscribeTheme, getClientTheme, getServerTheme);

  function setTheme(next: Theme) {
    window.localStorage.setItem(THEME_STORAGE_KEY, next);
    document.documentElement.dataset.theme = next;
    window.dispatchEvent(new Event(THEME_CHANGE_EVENT));
  }

  return { theme, setTheme };
}

function getServerTheme(): Theme {
  return "light";
}

function getClientTheme(): Theme {
  const saved = window.localStorage.getItem(THEME_STORAGE_KEY);
  const theme = saved === "light" || saved === "dark" ? saved : "light";
  document.documentElement.dataset.theme = theme;
  return theme;
}

function subscribeTheme(onStoreChange: () => void) {
  window.addEventListener("storage", onStoreChange);
  window.addEventListener(THEME_CHANGE_EVENT, onStoreChange);
  return () => {
    window.removeEventListener("storage", onStoreChange);
    window.removeEventListener(THEME_CHANGE_EVENT, onStoreChange);
  };
}
