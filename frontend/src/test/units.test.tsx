import { act, render, renderHook, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { vi } from "vitest";
import { AnalyzeError, analyzeMessage } from "../api/client";
import { ThemeSwitch } from "../components/Header";
import { summarizeResult } from "../lib/status";
import { countCharacters, formatDate, highlightEvidence } from "../lib/text";
import { THEME_STORAGE_KEY, ThemeProvider, useTheme } from "../lib/theme";

afterEach(() => vi.unstubAllGlobals());

function respond(body: unknown, status: number) {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status })));
}

describe("analyzeMessage", () => {
  test.each([
    [{ detail: [{ loc: ["body", "message"], msg: "Value error, message must not be blank", type: "value_error" }] }, "blank"],
    [{ detail: [{ loc: ["body", "message"], msg: "String should have at most 5000 characters", type: "string_too_long" }] }, "too_long"],
    [{ detail: [{ loc: ["body"], msg: "JSON decode error", type: "json_invalid" }] }, "invalid"],
  ])("maps a 422 response to %#", async (body, kind) => {
    respond(body, 422);
    await expect(analyzeMessage("x")).rejects.toMatchObject({ kind });
  });

  test("rejects a response that does not match the API contract", async () => {
    respond({ findings: [] }, 200);
    await expect(analyzeMessage("x")).rejects.toBeInstanceOf(AnalyzeError);
  });

  test("times out", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((_url: string, init: RequestInit) => new Promise((_resolve, reject) => init.signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError"))))),
    );
    await expect(analyzeMessage("x", { timeoutMs: 20 })).rejects.toMatchObject({ kind: "timeout" });
  });
});

describe("text helpers", () => {
  test("counts code points, like the API", () => {
    expect(countCharacters("OTP")).toBe(3);
    expect(countCharacters("🙂🙂")).toBe(2);
    expect(countCharacters("ओटीपी")).toBe(5);
  });

  test("formats ISO dates without shifting the day", () => {
    expect(formatDate("2025-03-06")).toBe("6 Mar 2025");
    expect(formatDate("not a date")).toBe("not a date");
  });

  test("highlights evidence that appears word for word, and skips shortened evidence", () => {
    const parts = highlightEvidence("URGENT: share your OTP now", ["URGENT", "share your OTP", "missing…"]);
    expect(parts.filter((part) => part.highlighted).map((part) => part.text)).toEqual(["URGENT", "share your OTP"]);
    expect(parts.map((part) => part.text).join("")).toBe("URGENT: share your OTP now");
  });

  test("merges overlapping evidence into one highlight", () => {
    const message = "Update KYC at http://bit.ly/kyc-update and share the OTP";
    const parts = highlightEvidence(message, ["http://bit.ly/kyc-update", "update and share the OTP"]);
    expect(parts).toEqual([
      { text: "Update KYC at ", highlighted: false },
      { text: "http://bit.ly/kyc-update and share the OTP", highlighted: true },
    ]);
  });

  test("summaries come from findings only and never claim safety", () => {
    expect(summarizeResult([]).title).not.toMatch(/safe/i);
    expect(summarizeResult([]).body).toMatch(/does not mean the message is safe/);
    expect(summarizeResult([{ category: "link", explanation: "", evidence: "" }]).title).toBe("We noticed 1 warning sign");
  });
});

describe("theme", () => {
  function stubSystemDark(dark: boolean) {
    vi.stubGlobal("matchMedia", (query: string) => ({
      matches: dark && query.includes("dark"),
      media: query,
      addEventListener: () => {},
      removeEventListener: () => {},
    }));
    window.matchMedia = globalThis.matchMedia;
  }

  const wrapper = ({ children }: { children: ReactNode }) => <ThemeProvider>{children}</ThemeProvider>;

  test("system mode follows prefers-color-scheme", () => {
    stubSystemDark(true);
    const { result } = renderHook(() => useTheme(), { wrapper });

    expect(result.current.preference).toBe("system");
    expect(result.current.resolved).toBe("dark");
    expect(document.documentElement.dataset.theme).toBe("dark");
  });

  test("switching theme updates the page and is remembered", async () => {
    stubSystemDark(false);
    const user = userEvent.setup();
    render(<ThemeSwitch />, { wrapper });

    await user.click(screen.getByRole("button", { name: "Dark theme" }));
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe("dark");
    expect(screen.getByRole("button", { name: "Dark theme" })).toHaveAttribute("aria-pressed", "true");

    await user.click(screen.getByRole("button", { name: "Light theme" }));
    expect(document.documentElement.dataset.theme).toBe("light");

    await user.click(screen.getByRole("button", { name: "System theme" }));
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe("system");
    expect(document.documentElement.dataset.theme).toBe("light");
  });

  test("a saved preference is restored", () => {
    stubSystemDark(false);
    window.localStorage.setItem(THEME_STORAGE_KEY, "dark");
    const { result } = renderHook(() => useTheme(), { wrapper });

    act(() => undefined);
    expect(result.current.resolved).toBe("dark");
  });
});
