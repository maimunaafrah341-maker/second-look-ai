import type { AnalyzeResponse } from "./types";

export type ApiErrorKind = "blank" | "too_long" | "invalid" | "network" | "timeout" | "server";

/** A failed analysis, described so the interface can explain it in plain language. */
export class AnalyzeError extends Error {
  constructor(
    readonly kind: ApiErrorKind,
    readonly status?: number,
  ) {
    super(kind);
    this.name = "AnalyzeError";
  }
}

export const DEFAULT_TIMEOUT_MS = 75_000;

function apiBase(): string {
  return (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");
}

interface ValidationDetail {
  type?: string;
}

function validationKind(body: unknown): ApiErrorKind {
  const detail = (body as { detail?: ValidationDetail[] } | null)?.detail;
  const types = Array.isArray(detail) ? detail.map((item) => item?.type) : [];
  if (types.includes("string_too_long")) return "too_long";
  if (types.includes("value_error")) return "blank";
  return "invalid";
}

function looksLikeAnalysis(body: unknown): body is AnalyzeResponse {
  const value = body as Partial<AnalyzeResponse> | null;
  return Boolean(
    value &&
      Array.isArray(value.findings) &&
      typeof value.notice === "string" &&
      value.guidance &&
      Array.isArray(value.guidance.matches) &&
      value.classifier &&
      typeof value.classifier.status === "string" &&
      value.language &&
      typeof value.language.detected === "string",
  );
}

interface AnalyzeOptions {
  signal?: AbortSignal;
  timeoutMs?: number;
}

/** Send a message to POST /analyze. Throws AnalyzeError on any failure. */
export async function analyzeMessage(message: string, options: AnalyzeOptions = {}): Promise<AnalyzeResponse> {
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, options.timeoutMs ?? DEFAULT_TIMEOUT_MS);
  const onAbort = () => controller.abort();
  options.signal?.addEventListener("abort", onAbort);

  try {
    let response: Response;
    try {
      response = await fetch(`${apiBase()}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ message }),
        signal: controller.signal,
      });
    } catch (error) {
      if (timedOut) throw new AnalyzeError("timeout");
      if (options.signal?.aborted) throw error;
      throw new AnalyzeError("network");
    }

    const body: unknown = await response.json().catch(() => null);
    if (response.status === 422) throw new AnalyzeError(validationKind(body), 422);
    if (!response.ok) throw new AnalyzeError("server", response.status);
    if (!looksLikeAnalysis(body)) throw new AnalyzeError("server", response.status);
    return body;
  } finally {
    clearTimeout(timer);
    options.signal?.removeEventListener("abort", onAbort);
  }
}
