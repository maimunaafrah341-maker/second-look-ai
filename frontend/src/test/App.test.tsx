import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import App, { SLOW_AFTER_MS } from "../App";
import type { AnalyzeResponse } from "../api/types";
import { ThemeProvider } from "../lib/theme";
import benign from "./fixtures/benign.json";
import englishScam from "./fixtures/english-scam.json";
import hindiScam from "./fixtures/hindi-scam.json";

// Fixtures are real responses captured from the backend's POST /analyze.
interface Fixture {
  message: string;
  response: AnalyzeResponse;
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function mockFetch(...responses: (Response | Error)[]) {
  const fetchMock = vi.fn();
  for (const response of responses) {
    if (response instanceof Error) fetchMock.mockRejectedValueOnce(response);
    else fetchMock.mockResolvedValueOnce(response);
  }
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function renderApp() {
  const user = userEvent.setup();
  render(
    <ThemeProvider>
      <App />
    </ThemeProvider>,
  );
  const input = screen.getByLabelText("Message to check");
  const analyze = screen.getByRole("button", { name: /analyze message/i });
  return { user, input, analyze };
}

async function analyzeFixture(fixture: Fixture) {
  const fetchMock = mockFetch(jsonResponse(fixture.response));
  const view = renderApp();
  await view.user.click(view.input);
  await view.user.paste(fixture.message);
  await view.user.click(view.analyze);
  await screen.findByRole("heading", { level: 2, name: /warning sign/i });
  return { ...view, fetchMock };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

test("sends the message to POST /analyze and shows the results in the agreed order", async () => {
  const { fetchMock } = await analyzeFixture(englishScam as Fixture);

  expect(fetchMock).toHaveBeenCalledTimes(1);
  const [url, init] = fetchMock.mock.calls[0];
  expect(url).toBe("/analyze");
  expect(init.method).toBe("POST");
  expect(JSON.parse(init.body)).toEqual({ message: englishScam.message });

  const headings = screen
    .getAllByRole("heading", { level: 3 })
    .map((heading) => heading.textContent)
    .filter((text) => ["Warning signs", "What official sources say", "Safer next steps", "Auxiliary signal"].includes(text ?? ""));
  expect(headings).toEqual(["Warning signs", "What official sources say", "Safer next steps", "Auxiliary signal"]);
  expect(screen.getByRole("heading", { name: "We noticed 3 warning signs" })).toHaveFocus();
});

test("renders each warning sign with its category, explanation and original evidence", async () => {
  await analyzeFixture(englishScam as Fixture);

  const findings = (englishScam as Fixture).response.findings;
  for (const finding of findings) {
    expect(screen.getByText(`“${finding.evidence}”`)).toBeInTheDocument();
    expect(screen.getByText(finding.explanation)).toBeInTheDocument();
  }
  expect(screen.getByRole("heading", { name: "Asks for an OTP, PIN or password" })).toBeInTheDocument();
  // Every piece of evidence is highlighted inside the original message.
  const highlighted = Array.from(document.querySelectorAll(".submitted__text mark")).map((mark) => mark.textContent ?? "");
  for (const finding of findings) {
    expect(highlighted.some((text) => text.includes(finding.evidence))).toBe(true);
  }
});

test("renders official guidance with publisher, section, dates and the real source link", async () => {
  await analyzeFixture(englishScam as Fixture);

  const match = (englishScam as Fixture).response.guidance.matches[0];
  const card = screen.getByRole("heading", { name: match.topic }).closest("li")!;
  const scoped = within(card);
  expect(scoped.getByText(match.source.publisher)).toBeInTheDocument();
  expect(scoped.getByText(match.source.section)).toBeInTheDocument();
  expect(scoped.getByText(match.summary_note)).toBeInTheDocument();
  expect(scoped.getByText("Retrieved")).toBeInTheDocument();
  // This CERT-In leaflet is undated, so no publication date is shown.
  expect(match.source.published).toBeNull();
  expect(scoped.queryByText("Published")).not.toBeInTheDocument();
  const link = scoped.getByRole("link", { name: /view official source/i });
  expect(link).toHaveAttribute("href", match.source.url);
  expect(link).toHaveAttribute("target", "_blank");
  expect(link).toHaveAttribute("rel", "noopener noreferrer");
});

test("shows the language estimate and a not-applicable classifier calmly for Hindi", async () => {
  await analyzeFixture(hindiScam as Fixture);

  const response = (hindiScam as Fixture).response;
  expect(screen.getByText("Hindi")).toBeInTheDocument();
  expect(screen.getByText("Partial checks")).toBeInTheDocument();
  expect(screen.getByText(response.language.notice)).toBeInTheDocument();

  const classifier = screen.getByRole("heading", { name: "Auxiliary signal" }).closest("section")!;
  expect(within(classifier).getByText("Not applied to this message")).toBeInTheDocument();
  expect(within(classifier).getByText(response.classifier.notice)).toBeInTheDocument();
  expect(within(classifier).getByText("Experimental")).toBeInTheDocument();
});

test("the classifier never shows a score, percentage, or verdict", async () => {
  await analyzeFixture(englishScam as Fixture);

  const classifier = screen.getByRole("heading", { name: "Auxiliary signal" }).closest("section")!;
  const text = classifier.textContent ?? "";
  expect(text).toContain("Resembles older English SMS spam");
  expect(text).toContain("It does not decide whether a message is fraudulent");
  // The notice says a "not spam-like" label "does not mean the message is safe"; nothing
  // should present a number, probability, or verdict.
  expect(text).not.toMatch(/\d+(\.\d+)?\s*%|probability|confidence|score|scam detected|fraud detected/i);
});

test("a message with no findings is not presented as safe", async () => {
  const fetchMock = mockFetch(jsonResponse((benign as Fixture).response));
  const { user, input, analyze } = renderApp();
  await user.type(input, (benign as Fixture).message);
  await user.click(analyze);

  const heading = await screen.findByRole("heading", { name: /didn't find the warning signs/i });
  expect(fetchMock).toHaveBeenCalledTimes(1);
  const summary = heading.closest(".summary") as HTMLElement;
  expect(summary).toHaveClass("summary--neutral");
  expect(within(summary).getByText(/does not mean the message is safe/i)).toBeInTheDocument();
  expect(screen.getByText((benign as Fixture).response.guidance.notice)).toBeInTheDocument();
});

test("shows a loading state, then a slow-start note while waiting", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  let resolveFetch!: (response: Response) => void;
  vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>((resolve) => (resolveFetch = resolve))));
  const { user, input, analyze } = renderApp();
  await user.type(input, "Please share your OTP");
  await user.click(analyze);

  expect(screen.getByRole("button", { name: /analyzing/i })).toBeDisabled();
  expect(screen.getByRole("status")).toHaveTextContent("Checking your message");
  expect(input).toHaveAttribute("readonly");

  await act(async () => {
    vi.advanceTimersByTime(SLOW_AFTER_MS + 100);
  });
  expect(screen.getByRole("status")).toHaveTextContent(/starting up/i);

  await act(async () => resolveFetch(jsonResponse((benign as Fixture).response)));
  await screen.findByRole("heading", { name: /didn't find the warning signs/i });
});

test("explains a network failure and lets the user try again", async () => {
  const fetchMock = mockFetch(new TypeError("Failed to fetch"), jsonResponse((englishScam as Fixture).response));
  const { user, input, analyze } = renderApp();
  await user.type(input, "Please share your OTP");
  await user.click(analyze);

  const alert = await screen.findByRole("alert");
  expect(alert).toHaveTextContent("We couldn't reach Second Look");

  await user.click(within(alert).getByRole("button", { name: /try again/i }));
  await screen.findByRole("heading", { name: "We noticed 3 warning signs" });
  expect(fetchMock).toHaveBeenCalledTimes(2);
});

test("explains a server error", async () => {
  mockFetch(jsonResponse({ detail: "Internal Server Error" }, 500));
  const { user, input, analyze } = renderApp();
  await user.type(input, "hello");
  await user.click(analyze);

  expect(await screen.findByRole("alert")).toHaveTextContent("Something went wrong on our side");
});

test("blocks an empty message without calling the API", async () => {
  const fetchMock = mockFetch();
  const { user, input, analyze } = renderApp();
  await user.type(input, "   ");
  await user.click(analyze);

  expect(screen.getByRole("alert")).toHaveTextContent("Paste or type a message to analyze.");
  expect(input).toHaveAttribute("aria-invalid", "true");
  expect(input).toHaveFocus();
  expect(fetchMock).not.toHaveBeenCalled();
});

test("blocks a message over 5,000 characters and counts emoji as one character", async () => {
  const fetchMock = mockFetch();
  const { user, input, analyze } = renderApp();

  await user.click(input);
  await user.paste("🙂".repeat(5000));
  expect(screen.getByText(/5,000 \/ 5,000/)).toBeInTheDocument();

  await user.paste("x");
  expect(screen.getByText(/5,001 \/ 5,000/)).toHaveClass("is-over");
  await user.click(analyze);
  expect(screen.getByRole("alert")).toHaveTextContent("longer than 5,000 characters");
  expect(fetchMock).not.toHaveBeenCalled();
});

test("Clear empties the message and removes the results", async () => {
  const { user } = await analyzeFixture(englishScam as Fixture);

  await user.click(screen.getByRole("button", { name: "Clear" }));

  expect(screen.getByLabelText("Message to check")).toHaveValue("");
  expect(screen.queryByRole("heading", { name: /warning signs/i, level: 2 })).not.toBeInTheDocument();
});

test("screenshot upload is clearly not available and does nothing", async () => {
  const fetchMock = mockFetch();
  const { user } = renderApp();
  const upload = screen.getByRole("button", { name: /upload screenshot/i });

  expect(upload).toHaveAttribute("aria-disabled", "true");
  expect(upload).toHaveTextContent("Not supported — paste the text instead");
  await user.click(upload);
  expect(document.querySelector('input[type="file"]')).toBeNull();
  expect(fetchMock).not.toHaveBeenCalled();
});

test("examples fill the message box", async () => {
  const { user, input } = renderApp();

  await user.click(screen.getByRole("button", { name: /try an example/i }));
  await user.click(screen.getByRole("button", { name: /genuine bank otp notice/i }));

  expect((input as HTMLTextAreaElement).value).toMatch(/Never share your OTP/);
});

test("interface language is separate from message analysis", () => {
  renderApp();
  const select = screen.getByLabelText(/interface language/i) as HTMLSelectElement;

  expect(select.value).toBe("en");
  const enabled = Array.from(select.options).filter((option) => !option.disabled);
  expect(enabled.map((option) => option.value)).toEqual(["en"]);
});

test("responsive sanity: one main landmark, labelled navigation, and a mobile menu toggle", async () => {
  const { user } = renderApp();

  expect(screen.getAllByRole("main")).toHaveLength(1);
  expect(screen.getByRole("navigation", { name: "Main" })).toBeInTheDocument();
  const toggle = screen.getByRole("button", { name: "Open menu" });
  expect(toggle).toHaveAttribute("aria-expanded", "false");
  await user.click(toggle);
  expect(screen.getByRole("button", { name: "Close menu" })).toHaveAttribute("aria-expanded", "true");
  await waitFor(() => expect(document.querySelector(".site-header__menu")).toHaveClass("is-open"));
});
