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

// Types for GET /next-steps: fixed steps for what happened after the message.

export interface StepAction {
  label: string;
  href: string;
}

export interface NextStep {
  topic: string;
  summary: string;
  summary_note: string;
  source: GuidanceSource;
  action: StepAction | null;
}

export interface NextStepSituation {
  id: string;
  label: string;
  steps: NextStep[];
}

export interface NextStepsResponse {
  situations: NextStepSituation[];
  notice: string;
}

// Types for POST /agent: the optional agent, which sends the message to a language model.

export type AgentStatus = "finished" | "needs_input" | "step_limit" | "rejected" | "unavailable";

export interface AgentOption {
  id: string;
  label: string;
}

export interface AgentStep {
  step: number;
  provider: string | null;
  action: string;
  args: Record<string, unknown>;
  outcome: "ok" | "refused" | "rejected";
  detail: string;
  /** The model's one-line reason for the step, when it gave one that passed the server's check. */
  reason: string | null;
  /** What the action returned: part of an /analyze response, one next-steps situation, a report, or nothing. */
  result: unknown;
}

/** The report the agent can prepare: the English text, and the parts it was built from. */
export interface AgentReport {
  kind: "report";
  title: string;
  text: string;
  parts?: {
    date: string;
    message: string;
    answer_id: string | null;
    findings: { category: string; evidence: string }[];
    reporting: { summary: string; publisher: string; url: string };
  };
}

export interface AgentResponse {
  status: AgentStatus;
  text: string | null;
  question: string | null;
  options: AgentOption[];
  trace: AgentStep[];
  notice: string;
}
