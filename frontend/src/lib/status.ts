import type { Finding } from "../api/types";

export interface ResultSummary {
  tone: "attention" | "neutral";
  title: string;
  body: string;
}

/**
 * Summarise a result from the rule-based findings only. It never reads the classifier or
 * the guidance, and it never says a message is safe or fraudulent.
 */
export function summarizeResult(findings: Finding[]): ResultSummary {
  const count = findings.length;
  if (count > 0) {
    return {
      tone: "attention",
      title: `We noticed ${count} warning ${count === 1 ? "sign" : "signs"}`,
      body: "Review them below before you reply, click a link, share a code, or pay.",
    };
  }
  return {
    tone: "neutral",
    title: "We didn't find the warning signs we check for",
    body: "That does not mean the message is safe. Scams can avoid these patterns, so verify through an official channel before you act.",
  };
}
