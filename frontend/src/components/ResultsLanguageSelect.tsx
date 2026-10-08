import { useId } from "react";
import { RESULTS_LANGUAGES, type ResultsLanguage } from "../lib/resultsLanguage";

interface ResultsLanguageSelectProps {
  value: ResultsLanguage;
  onChange: (language: ResultsLanguage) => void;
}

/**
 * Chooses the language results are shown in. It is not an interface-language switch: the
 * rest of the page stays in English, and the message and its analysis are not affected.
 */
export function ResultsLanguageSelect({ value, onChange }: ResultsLanguageSelectProps) {
  const id = useId();
  return (
    <div className="results-language">
      <label htmlFor={id} className="results-language__label">
        Results language
      </label>
      <select
        id={id}
        className="results-language__select"
        value={value}
        onChange={(event) => onChange(event.target.value as ResultsLanguage)}
      >
        {RESULTS_LANGUAGES.map((option) => (
          <option key={option.value} value={option.value} lang={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}
