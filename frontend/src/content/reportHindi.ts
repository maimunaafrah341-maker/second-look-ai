// The agent's report, laid out in Hindi from the parts the API sends. The English report is
// assembled by the backend (backend/app/report.py); this follows it line for line.
//
// Written by the project and not reviewed by a language specialist. The person's message,
// the quoted excerpts, the publisher's name and the link are never translated.

import type { AgentReport } from "../api/types";
import { localizeApiText } from "./apiHindi";
import { RESULTS_TEXT } from "./resultsText";

export const SHOW_ENGLISH_REPORT = "अंग्रेज़ी में देखें";
export const SHOW_HINDI_REPORT = "हिन्दी में देखें";

const NOT_ANSWERED = "नहीं बताया";
const NO_FINDINGS =
  "Second Look जिन संकेतों की जाँच करता है, उनमें से कोई नहीं मिला। यह केवल कुछ ही संकेत जाँचता है और दूसरे छूट सकते हैं।";

/** The report in Hindi, or null when the API sent no parts to build it from. */
export function hindiReport(report: AgentReport): string | null {
  const parts = report.parts;
  if (!parts) return null;
  const text = RESULTS_TEXT.hi;
  const signs = parts.findings.map(
    (finding) => `- ${text.categoryLabels[finding.category] ?? text.categoryFallback}: "${finding.evidence}"`,
  );
  const answer = parts.answer_id ? text.situationLabels[parts.answer_id] : undefined;
  return [
    "संदिग्ध संदेश का रिकॉर्ड",
    `Second Look की मदद से ${parts.date} को तैयार किया गया।`,
    "यह मुझे मिले एक संदेश का रिकॉर्ड है। यह इस बात का निष्कर्ष नहीं है कि संदेश धोखाधड़ी है।",
    "",
    "संदेश, ठीक वैसा जैसा मुझे मिला:",
    parts.message,
    "",
    `अब तक मैंने क्या किया है: ${answer ?? NOT_ANSWERED}`,
    "",
    "Second Look की नियम-आधारित जाँच में दिखे चेतावनी संकेत:",
    ...(signs.length > 0 ? signs : [NO_FINDINGS]),
    "",
    "शिकायत कहाँ करें:",
    `${localizeApiText(parts.reporting.summary, "hi")} (स्रोत: ${parts.reporting.publisher}, ${parts.reporting.url})`,
  ].join("\n");
}
