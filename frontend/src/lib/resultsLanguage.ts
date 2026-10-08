import { useCallback, useState } from "react";

/** The language results are presented in. It never changes the message or the analysis. */
export type ResultsLanguage = "en" | "hi";

export const RESULTS_LANGUAGES: { value: ResultsLanguage; label: string }[] = [
  { value: "en", label: "English" },
  { value: "hi", label: "हिन्दी" },
];

export const RESULTS_LANGUAGE_STORAGE_KEY = "second-look-results-language";

function readPreference(): ResultsLanguage {
  try {
    const saved = window.localStorage.getItem(RESULTS_LANGUAGE_STORAGE_KEY);
    if (saved === "en" || saved === "hi") return saved;
  } catch {
    // Storage can be unavailable (private mode, blocked site data); fall back to English.
  }
  return "en";
}

/** The saved results language, English by default, remembered the same way as the theme. */
export function useResultsLanguage(): [ResultsLanguage, (language: ResultsLanguage) => void] {
  const [language, setLanguageState] = useState<ResultsLanguage>(readPreference);

  const setLanguage = useCallback((next: ResultsLanguage) => {
    setLanguageState(next);
    try {
      window.localStorage.setItem(RESULTS_LANGUAGE_STORAGE_KEY, next);
    } catch {
      // Not saved; the choice still applies for this visit.
    }
  }, []);

  return [language, setLanguage];
}
