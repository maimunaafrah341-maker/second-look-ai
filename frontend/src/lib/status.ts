import type { Finding, LanguageCoverage, LanguageTag } from "../api/types";
import { RESULTS_TEXT } from "../content/resultsText";
import type { ResultsLanguage } from "./resultsLanguage";

export interface ResultSummary {
  tone: "attention" | "neutral";
  title: string;
  body: string;
}

/**
 * Summarise a result from the rule-based findings and how well the message's language is
 * covered. It never reads the classifier or the guidance, and it never says a message is
 * safe or fraudulent. Only a fully covered message can get the ordinary "we didn't find"
 * summary: when the language is checked partly or not at all, it says the check was
 * incomplete instead. This follows the API's coverage value, never the language's name.
 */
export function summarizeResult(
  findings: Finding[],
  coverage: LanguageCoverage = "supported",
  language: ResultsLanguage = "en",
  detected?: LanguageTag,
): ResultSummary {
  const text = RESULTS_TEXT[language];
  // No language was identified at all, so the wording must not refer to "this language".
  const unidentified = detected === "unknown";
  const count = findings.length;
  if (count > 0) {
    return {
      tone: "attention",
      title: text.summaryFound(count),
      body:
        coverage === "unsupported"
          ? `${text.summaryFoundBody} ${unidentified ? text.summaryUnidentifiedFoundNote : text.summaryUnsupportedFoundNote}`
          : text.summaryFoundBody,
    };
  }
  if (coverage === "unsupported") {
    return {
      tone: "neutral",
      title: text.summaryUnsupportedTitle,
      body: unidentified ? text.summaryUnidentifiedBody : text.summaryUnsupportedBody,
    };
  }
  if (coverage === "partial") {
    return { tone: "neutral", title: text.summaryUnsupportedTitle, body: text.summaryPartialBody };
  }
  return { tone: "neutral", title: text.summaryNoneTitle, body: text.summaryNoneBody };
}
