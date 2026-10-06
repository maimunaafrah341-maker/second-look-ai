// Types for POST /analyze, matching the FastAPI response models in backend/app/main.py.

export const MAX_MESSAGE_LENGTH = 5000;

export interface AnalyzeRequest {
  message: string;
}

export type FindingCategory = "urgency_pressure" | "credential_request" | "link" | "payment_demand";

export interface Finding {
  category: FindingCategory | string;
  explanation: string;
  /** Excerpt from the user's own message, in its original language and script. */
  evidence: string;
}

export interface GuidanceSource {
  title: string;
  publisher: string;
  url: string;
  published: string | null;
  retrieved: string;
  section: string;
}

export interface GuidanceMatch {
  topic: string;
  summary: string;
  summary_note: string;
  source: GuidanceSource;
  matched_terms: string[];
}

export interface Guidance {
  matches: GuidanceMatch[];
  notice: string;
}

export type ClassifierStatus = "ok" | "unavailable" | "not_applicable";
export type ClassifierLabel = "spam_like" | "not_spam_like";

export interface ClassifierModel {
  name: string;
  training_data: string;
  model_sha256: string;
}

export interface ClassifierSection {
  status: ClassifierStatus;
  label: ClassifierLabel | null;
  model: ClassifierModel | null;
  notice: string;
}

export type LanguageTag = "en" | "hi" | "hi-Latn" | "te" | "ur" | "bn" | "mixed" | "unknown";
export type LanguageCoverage = "supported" | "partial" | "unsupported";

export interface LanguageSection {
  detected: LanguageTag;
  method: string;
  coverage: LanguageCoverage;
  notice: string;
}

export interface AnalyzeResponse {
  findings: Finding[];
  notice: string;
  guidance: Guidance;
  classifier: ClassifierSection;
  language: LanguageSection;
}
