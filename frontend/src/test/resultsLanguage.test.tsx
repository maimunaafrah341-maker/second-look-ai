import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import App from "../App";
import { clearNextStepsCache } from "../api/client";
import type { AnalyzeResponse } from "../api/types";
import { API_TEXT_HINDI, localizeApiText, localizeExplanation } from "../content/apiHindi";
import { HINDI_EXPLANATION_LABEL, HINDI_PRESENTATION_NOTE, RESULTS_TEXT } from "../content/resultsText";
import { RESULTS_LANGUAGE_STORAGE_KEY } from "../lib/resultsLanguage";
import { summarizeResult } from "../lib/status";
import { ThemeProvider } from "../lib/theme";
import fixedText from "./fixtures/api-fixed-text.json";
import bengaliUnsupported from "./fixtures/bengali-unsupported.json";
import benign from "./fixtures/benign.json";
import englishScam from "./fixtures/english-scam.json";
import hindiBenign from "./fixtures/hindi-benign.json";
import hindiScam from "./fixtures/hindi-scam.json";
import mixedNoFindings from "./fixtures/mixed-no-findings.json";
import nextSteps from "./fixtures/next-steps.json";
import romanisedHindiBenign from "./fixtures/romanised-hindi-benign.json";
import romanisedHindiScam from "./fixtures/romanised-hindi-scam.json";
import teluguUnsupported from "./fixtures/telugu-unsupported.json";
import teluguWithLink from "./fixtures/telugu-with-link.json";
import unidentifiedLanguage from "./fixtures/unidentified-language.json";
import urduUnsupported from "./fixtures/urdu-unsupported.json";

// Fixtures are real responses captured from the backend. api-fixed-text.json lists every
// fixed English text the backend can send, read from its code and guidance corpus.
interface Fixture {
  message: string;
  response: AnalyzeResponse;
}

const DEVANAGARI = /[ऀ-ॿ]/;

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } });
}

function mockFetch(...bodies: unknown[]) {
  const fetchMock = vi.fn();
  for (const body of bodies) fetchMock.mockResolvedValueOnce(jsonResponse(body));
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
  return user;
}

async function analyze(fixture: Fixture, ...more: unknown[]) {
  const fetchMock = mockFetch(fixture.response, ...more);
  const user = renderApp();
  const input = screen.getByLabelText("Message to check");
  await user.click(input);
  await user.paste(fixture.message);
  await user.click(screen.getByRole("button", { name: /analyze message/i }));
  await screen.findByRole("heading", { level: 3, name: /^(Your message|आपका संदेश)$/ });
  return { user, fetchMock, input: input as HTMLTextAreaElement };
}

const selector = () => screen.getAllByLabelText("Results language")[0] as HTMLSelectElement;
const results = () => document.querySelector(".results__body") as HTMLElement;
const headings = (level: number) => within(results()).getAllByRole("heading", { level }).map((heading) => heading.textContent);

afterEach(() => {
  vi.unstubAllGlobals();
  clearNextStepsCache();
});

// --- The dictionaries ---------------------------------------------------------------------

describe("Hindi dictionary", () => {
  const apiTexts: string[] = [
    ...Object.values(fixedText.finding_explanations),
    ...fixedText.link_traits,
    fixedText.findings_notice,
    ...fixedText.guidance_notices,
    fixedText.summary_note,
    ...Object.values(fixedText.classifier_notices),
    fixedText.classifier_training_data,
    ...Object.values(fixedText.language_notices),
    ...fixedText.passages.flatMap((passage) => [passage.topic, passage.summary]),
    fixedText.next_steps_notice,
    ...fixedText.next_step_actions,
  ];

  test.each(apiTexts)("has Hindi for the API text: %s", (english) => {
    expect(API_TEXT_HINDI[english]).toMatch(DEVANAGARI);
    expect(localizeApiText(english, "hi")).toBe(API_TEXT_HINDI[english]);
    expect(localizeApiText(english, "en")).toBe(english);
  });

  test("has no entry for English text the backend no longer sends", () => {
    expect(Object.keys(API_TEXT_HINDI).sort()).toEqual([...new Set(apiTexts)].sort());
  });

  test("has a Hindi label for every next-step choice, keyed by its id", () => {
    expect(Object.keys(RESULTS_TEXT.hi.situationLabels).sort()).toEqual(Object.keys(fixedText.next_step_situations).sort());
    for (const label of Object.values(RESULTS_TEXT.hi.situationLabels)) expect(label).toMatch(DEVANAGARI);
  });

  test("has a label for every warning-sign category, message language and coverage level, in both languages", () => {
    for (const language of ["en", "hi"] as const) {
      const text = RESULTS_TEXT[language];
      expect(Object.keys(text.categoryLabels).sort()).toEqual(Object.keys(fixedText.finding_explanations).sort());
      expect(Object.keys(text.languageLabels).sort()).toEqual(Object.keys(fixedText.language_notices).sort());
      expect(Object.keys(text.coverageLabels).sort()).toEqual(["partial", "supported", "unsupported"]);
      expect(Object.keys(text.classifierHeadlines).sort()).toEqual(["not_applicable", "not_spam_like", "spam_like", "unavailable"]);
      expect(text.safetySteps).toHaveLength(4);
    }
  });

  test("English and Hindi wording cover the same things, and the Hindi is in Hindi", () => {
    expect(Object.keys(RESULTS_TEXT.hi).sort()).toEqual(Object.keys(RESULTS_TEXT.en).sort());
    for (const [key, value] of Object.entries(RESULTS_TEXT.hi)) {
      if (typeof value === "string") expect(value, key).toMatch(DEVANAGARI);
    }
    expect(RESULTS_TEXT.hi.summaryFound(1)).toMatch(DEVANAGARI);
    expect(RESULTS_TEXT.hi.summaryFound(3)).toContain("3");
    expect(RESULTS_TEXT.hi.classifierModel("X")).toContain("X");
  });

  test("the Hindi keeps the warnings and makes no claim of review or safety", () => {
    const hindi = [...Object.values(API_TEXT_HINDI), JSON.stringify(RESULTS_TEXT.hi), HINDI_PRESENTATION_NOTE].join(" ");

    expect(RESULTS_TEXT.hi.summaryNoneBody).toContain("इसका मतलब यह नहीं है कि संदेश सुरक्षित है");
    expect(RESULTS_TEXT.hi.summaryUnsupportedBody).toContain("इसका मतलब यह नहीं है कि संदेश सुरक्षित है");
    expect(HINDI_PRESENTATION_NOTE).toContain("समीक्षा नहीं की है");
    expect(HINDI_EXPLANATION_LABEL).toContain("आधिकारिक पाठ नहीं");
    // Every mention of "safe" is a denial, in every text.
    for (const sentence of hindi.split(/[।.]/)) {
      if (sentence.includes("सुरक्षित है")) expect(sentence).toContain("नहीं");
    }
    expect(hindi).not.toMatch(/विशेषज्ञों द्वारा सत्यापित|native-reviewed|verified by experts/i);
  });

  test("a link's details are translated only when every part is known", () => {
    const link = (englishScam as Fixture).response.findings.find((finding) => finding.category === "link")!;
    const hindi = localizeExplanation(link.explanation, "hi");

    expect(link.explanation).toContain(" This link ");
    expect(hindi).toContain("यह लिंक");
    expect(hindi).not.toMatch(/[A-Za-z]{6,}/);
    expect(localizeExplanation(link.explanation, "en")).toBe(link.explanation);
    // An unknown detail keeps the whole explanation in English, never half and half.
    const unknown = `${fixedText.finding_explanations.link} This link does something new.`;
    expect(localizeExplanation(unknown, "hi")).toBe(unknown);
    expect(localizeApiText("Some new server text", "hi")).toBe("Some new server text");
  });
});

// --- Summaries ---------------------------------------------------------------------------

describe("result summary", () => {
  const finding = { category: "link", explanation: "", evidence: "" };

  test("an unanalysed language is never reported as having no warning signs", () => {
    for (const language of ["en", "hi"] as const) {
      const text = RESULTS_TEXT[language];
      const summary = summarizeResult([], "unsupported", language);

      expect(summary.title).toBe(text.summaryUnsupportedTitle);
      expect(summary.title).not.toBe(text.summaryNoneTitle);
      expect(summary.tone).toBe("neutral");
      expect(summarizeResult([finding], "unsupported", language).body).toContain(text.summaryUnsupportedFoundNote);
      expect(summarizeResult([finding], "partial", language).body).toBe(text.summaryFoundBody);
    }
    // The agreed wording, word for word, in both results languages.
    expect(summarizeResult([], "unsupported", "en")).toEqual({
      tone: "neutral",
      title: "This message hasn't been fully checked",
      body: "We can check links, rupee amounts, and some English terms, but we may miss warning signs in this language. This does not mean the message is safe.",
    });
    expect(summarizeResult([], "unsupported", "hi")).toEqual({
      tone: "neutral",
      title: "इस संदेश की पूरी तरह जाँच नहीं हो सकी",
      body: "हम लिंक, रुपये की रकम और कुछ अंग्रेज़ी शब्दों की जाँच कर सकते हैं, लेकिन इस भाषा में चेतावनी के संकेत छूट सकते हैं। इसका मतलब यह नहीं है कि संदेश सुरक्षित है।",
    });
    expect(summarizeResult([], "supported").title).toBe("We didn't find the warning signs we check for");
    // Partly covered messages get the incomplete-check summary too, with their own body.
    expect(summarizeResult([], "partial", "en")).toEqual({
      tone: "neutral",
      title: "This message hasn't been fully checked",
      body: "We could check only some of the wording in this message, so we may miss warning signs. This does not mean the message is safe.",
    });
    expect(summarizeResult([], "partial", "hi").title).toBe("इस संदेश की पूरी तरह जाँच नहीं हो सकी");
    expect(summarizeResult([], "partial", "hi").body).toBe(RESULTS_TEXT.hi.summaryPartialBody);
    for (const language of ["en", "hi"] as const) {
      expect(summarizeResult([], "supported", language).title).toBe(RESULTS_TEXT[language].summaryNoneTitle);
      expect(summarizeResult([], "supported", language).body).toBe(RESULTS_TEXT[language].summaryNoneBody);
    }
    expect(summarizeResult([], "partial", "hi").body).toContain("इसका मतलब यह नहीं है कि संदेश सुरक्षित है");
  });
});

// --- The selector ------------------------------------------------------------------------

test("results are in English by default", async () => {
  await analyze(englishScam as Fixture);

  expect(selector().value).toBe("en");
  expect(headings(2)).toEqual(["We noticed 3 warning signs"]);
  expect(screen.queryByText(HINDI_PRESENTATION_NOTE)).toBeNull();
  expect(window.localStorage.getItem(RESULTS_LANGUAGE_STORAGE_KEY)).toBeNull();
});

test.each([
  ["English", englishScam as Fixture, "हमें 3 चेतावनी संकेत मिले"],
  ["Hindi", hindiScam as Fixture, "हमें 2 चेतावनी संकेत मिले"],
  ["Romanized Hindi", romanisedHindiScam as Fixture, "हमें 2 चेतावनी संकेत मिले"],
])("%s input can be shown in Hindi and back in English, with no new request", async (_name, fixture, hindiTitle) => {
  const { user, fetchMock, input } = await analyze(fixture);
  const englishTitle = headings(2)[0];
  const evidence = () => [...results().querySelectorAll("blockquote")].map((quote) => quote.textContent);
  const links = () => [...results().querySelectorAll(".guidance__link")].map((link) => link.getAttribute("href"));
  const sourceLines = () => [...results().querySelectorAll('[lang="en"]')].map((element) => element.textContent);
  const before = { evidence: evidence(), links: links(), sources: sourceLines().filter((line) => !DEVANAGARI.test(line ?? "")) };

  await user.selectOptions(selector(), "hi");

  // Presentation is Hindi.
  expect(headings(2)).toEqual([hindiTitle]);
  expect(headings(3)).toEqual(["आपका संदेश", "चेतावनी संकेत", "आधिकारिक स्रोत क्या कहते हैं", "सुरक्षित अगले कदम", "आगे क्या हुआ?", "सहायक संकेत"]);
  const hindi = RESULTS_TEXT.hi;
  for (const finding of fixture.response.findings) {
    expect(within(results()).getByRole("heading", { level: 4, name: hindi.categoryLabels[finding.category] })).toBeInTheDocument();
    expect(within(results()).getByText(localizeExplanation(finding.explanation, "hi"), { exact: false })).toBeInTheDocument();
  }
  expect(within(results()).getByText(API_TEXT_HINDI[fixture.response.notice])).toBeInTheDocument();
  expect(within(results()).getByText(API_TEXT_HINDI[fixture.response.guidance.notice])).toBeInTheDocument();
  expect(within(results()).getByText(API_TEXT_HINDI[fixture.response.language.notice])).toBeInTheDocument();
  expect(within(results()).getByText(API_TEXT_HINDI[fixture.response.classifier.notice])).toBeInTheDocument();
  expect(within(results()).getByRole("heading", { level: 4, name: hindi.safetySteps[3].title })).toBeInTheDocument();
  expect(screen.getByText(HINDI_PRESENTATION_NOTE)).toBeInTheDocument();
  // Guidance summaries are shown in Hindi, labelled as Second Look's translation, with the English kept.
  for (const match of fixture.response.guidance.matches) {
    expect(within(results()).getByRole("heading", { level: 4, name: API_TEXT_HINDI[match.topic] })).toBeInTheDocument();
    expect(within(results()).getByText(API_TEXT_HINDI[match.summary])).toBeInTheDocument();
    expect(within(results()).getByText(match.summary, { exact: false })).toBeInTheDocument();
  }
  expect(within(results()).getAllByText(HINDI_EXPLANATION_LABEL)).toHaveLength(fixture.response.guidance.matches.length);

  // The message, its evidence and the official source details are untouched.
  expect(evidence()).toEqual(before.evidence);
  expect(evidence()).toEqual(fixture.response.findings.map((finding) => `“${finding.evidence}”`));
  expect(results().querySelector(".submitted__text")?.textContent).toBe(fixture.message);
  expect(input.value).toBe(fixture.message);
  expect(links()).toEqual(before.links);
  expect(links()).toEqual(fixture.response.guidance.matches.map((match) => match.source.url));
  for (const match of fixture.response.guidance.matches) {
    expect(sourceLines()).toContain(match.source.publisher);
    expect(sourceLines()).toContain(match.source.title);
    expect(sourceLines()).toContain(match.source.section);
  }
  for (const line of before.sources) expect(sourceLines()).toContain(line);

  // No request was made for the switch, and the one request carried only the message.
  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ message: fixture.message });

  await user.selectOptions(selector(), "en");

  expect(headings(2)).toEqual([englishTitle]);
  expect(headings(3)).toEqual(["Your message", "Warning signs", "What official sources say", "Safer next steps", "What happened next?", "Auxiliary signal"]);
  expect(screen.queryByText(HINDI_EXPLANATION_LABEL)).toBeNull();
  expect(evidence()).toEqual(before.evidence);
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

test("the choice is remembered for later analyses and later visits, and is never sent", async () => {
  const fetchMock = mockFetch((hindiScam as Fixture).response, (englishScam as Fixture).response);
  const user = renderApp();

  // Chosen before any analysis.
  await user.selectOptions(selector(), "hi");
  expect(window.localStorage.getItem(RESULTS_LANGUAGE_STORAGE_KEY)).toBe("hi");

  const input = screen.getByLabelText("Message to check");
  await user.click(input);
  await user.paste(hindiScam.message);
  await user.click(screen.getByRole("button", { name: /analyze message/i }));
  expect(await screen.findByRole("heading", { level: 2, name: "हमें 2 चेतावनी संकेत मिले" })).toBeInTheDocument();

  // A second analysis keeps the choice.
  await user.click(within(results()).getByRole("button", { name: "दूसरा संदेश जाँचें" }));
  await user.click(input);
  await user.paste(englishScam.message);
  await user.click(screen.getByRole("button", { name: /analyze message/i }));
  expect(await screen.findByRole("heading", { level: 2, name: "हमें 3 चेतावनी संकेत मिले" })).toBeInTheDocument();

  for (const call of fetchMock.mock.calls) {
    expect(call[0]).toBe("/analyze");
    expect(Object.keys(JSON.parse(call[1].body))).toEqual(["message"]);
  }

  // A later visit starts in Hindi.
  cleanup();
  renderApp();
  expect(selector().value).toBe("hi");
});

test("the selector is labelled, keyboard-operable, and leaves the theme alone", async () => {
  const { user } = await analyze(englishScam as Fixture);

  const controls = screen.getAllByLabelText("Results language");
  expect(controls).toHaveLength(2);
  for (const control of controls) {
    expect(control.tagName).toBe("SELECT");
    expect(within(control).getAllByRole("option").map((option) => option.textContent)).toEqual(["English", "हिन्दी"]);
  }
  controls[1].focus();
  await user.keyboard("{ArrowDown}");
  await user.selectOptions(controls[1], "hi");
  // Both controls show the same choice.
  expect(controls.map((control) => (control as HTMLSelectElement).value)).toEqual(["hi", "hi"]);

  await user.click(screen.getByRole("button", { name: "Dark theme" }));
  expect(document.documentElement.dataset.theme).toBe("dark");
  expect(selector().value).toBe("hi");
  await user.selectOptions(selector(), "en");
  expect(document.documentElement.dataset.theme).toBe("dark");
  await user.click(screen.getByRole("button", { name: "Light theme" }));
  expect(document.documentElement.dataset.theme).toBe("light");
});

test("the rest of the page stays in English when results are in Hindi", async () => {
  const { user } = await analyze(englishScam as Fixture);
  await user.selectOptions(selector(), "hi");

  expect(screen.getByRole("heading", { name: "What did you receive?" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /analyze message/i })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: /what second look does/i })).toBeInTheDocument();
  expect(results()).toHaveAttribute("lang", "hi");
  expect(document.querySelector(".submitted__text")).toHaveAttribute("lang", "");
});

// --- Other result states -------------------------------------------------------------------

test("a message with no findings is not presented as safe, in Hindi either", async () => {
  const { user } = await analyze(benign as Fixture);
  await user.selectOptions(selector(), "hi");

  expect(headings(2)).toEqual(["जिन चेतावनी संकेतों की हम जाँच करते हैं, वे नहीं मिले"]);
  expect(within(results()).getAllByText(/इसका मतलब यह नहीं है कि संदेश सुरक्षित है/).length).toBeGreaterThanOrEqual(2);
  expect(within(results()).getByText(RESULTS_TEXT.hi.findingsNone)).toBeInTheDocument();
});

const UNANALYSED = [
  ["Telugu", teluguUnsupported as Fixture],
  ["Urdu", urduUnsupported as Fixture],
  ["Bengali", bengaliUnsupported as Fixture],
] as const;

describe.each(UNANALYSED)("a %s message with no findings", (_name, fixture) => {
  test.each(["en", "hi"] as const)("gets the unsupported-language explanation (%s results)", async (language) => {
    expect(fixture.response.findings).toEqual([]);
    expect(fixture.response.language.coverage).toBe("unsupported");
    const { user } = await analyze(fixture);
    if (language === "hi") await user.selectOptions(selector(), "hi");
    const text = RESULTS_TEXT[language];

    // Not "we didn't find the warning signs": the language was not analysed.
    expect(headings(2)).toEqual([text.summaryUnsupportedTitle]);
    expect(within(results()).queryByText(text.summaryNoneTitle)).toBeNull();
    expect(within(results()).queryByText(text.findingsNone)).toBeNull();
    expect(within(results()).getByText(text.summaryUnsupportedBody)).toBeInTheDocument();
    expect(within(results()).getByText(text.findingsNoneUnsupported)).toBeInTheDocument();
    expect(within(results()).getByText(text.coverageLabels.unsupported)).toBeInTheDocument();
    expect(within(results()).getByText(localizeApiText(fixture.response.language.notice, language))).toBeInTheDocument();
    expect(results().textContent).not.toMatch(/Partial checks|आंशिक जाँच|All checks apply|सभी जाँचें लागू/);
    expect(results().textContent).not.toMatch(/We didn't find|None of the warning signs|कोई इस संदेश में नहीं मिला/);
    // The message itself is shown exactly as sent.
    expect(results().querySelector(".submitted__text")?.textContent).toBe(fixture.message);
  });
});

test.each(["en", "hi"] as const)("a link found in an unanalysed language comes with a warning that more may be missed (%s results)", async (language) => {
  const fixture = teluguWithLink as Fixture;
  expect(fixture.response.findings.map((finding) => finding.category)).toEqual(["link"]);
  expect(fixture.response.language.coverage).toBe("unsupported");
  const { user } = await analyze(fixture);
  if (language === "hi") await user.selectOptions(selector(), "hi");
  const text = RESULTS_TEXT[language];

  expect(headings(2)).toEqual([text.summaryFound(1)]);
  expect(within(results()).getByText(`${text.summaryFoundBody} ${text.summaryUnsupportedFoundNote}`)).toBeInTheDocument();
  expect(results().textContent).toMatch(/other warning signs may have been missed|दूसरे चेतावनी संकेत छूट सकते हैं/);
  expect(within(results()).getByText(text.coverageLabels.unsupported)).toBeInTheDocument();
  expect(within(results()).getByText(localizeApiText(fixture.response.language.notice, language))).toBeInTheDocument();
  expect(results().textContent).not.toMatch(/Partial checks|आंशिक जाँच|All checks apply|सभी जाँचें लागू/);
  // The link is quoted exactly as it appeared.
  expect(results().querySelector("blockquote")?.textContent).toContain("http://bit.ly/kyc-update");
});

// The API could not identify any language (few or no letters, or an unrecognised script).
test.each(["en", "hi"] as const)("an unidentified language is not described as a language that is not analysed (%s results)", async (language) => {
  const fixture = unidentifiedLanguage as Fixture;
  expect(fixture.response.findings).toEqual([]);
  expect(fixture.response.language.detected).toBe("unknown");
  expect(fixture.response.language.coverage).toBe("unsupported");
  const { user } = await analyze(fixture);
  if (language === "hi") await user.selectOptions(selector(), "hi");
  const text = RESULTS_TEXT[language];

  expect(headings(2)).toEqual([text.summaryUnsupportedTitle]);
  expect(within(results()).getByText(text.summaryUnidentifiedBody)).toBeInTheDocument();
  expect(within(results()).getByText(text.findingsNoneUnidentified)).toBeInTheDocument();
  expect(within(results()).queryByText(text.summaryUnsupportedBody)).toBeNull();
  expect(within(results()).queryByText(text.findingsNoneUnsupported)).toBeNull();
  expect(within(results()).queryByText(text.summaryNoneTitle)).toBeNull();
  expect(within(results()).queryByText(text.findingsNone)).toBeNull();
  expect(results().textContent).not.toMatch(/this language|इस भाषा/i);
  expect(results().textContent).toMatch(/This does not mean the message is safe|इसका मतलब यह नहीं है कि संदेश सुरक्षित है/);
  expect(within(results()).getByText(text.languageLabels.unknown)).toBeInTheDocument();
  // The English-only classifier is not applied, so no spam-likeness is shown beside this summary.
  expect(fixture.response.classifier.status).toBe("not_applicable");
  expect(within(results()).getByText(text.classifierHeadlines.not_applicable)).toBeInTheDocument();
  expect(within(results()).queryByText(text.classifierHeadlines.spam_like)).toBeNull();
  expect(within(results()).queryByText(text.classifierHeadlines.not_spam_like)).toBeNull();
  expect(results().querySelector(".submitted__text")?.textContent).toBe(fixture.message);
});

test("the unidentified-language wording is exact, and known unsupported languages keep theirs", () => {
  const finding = { category: "link", explanation: "", evidence: "" };

  expect(summarizeResult([], "unsupported", "en", "unknown").body).toBe(
    "We couldn't fully check this message. Some warning signs may be missed. This does not mean the message is safe.",
  );
  expect(RESULTS_TEXT.en.findingsNonePartial).toBe("We didn't find these warning signs in the parts we could check.");
  for (const language of ["en", "hi"] as const) {
    const text = RESULTS_TEXT[language];
    expect(summarizeResult([], "unsupported", language, "unknown").title).toBe(text.summaryUnsupportedTitle);
    expect(summarizeResult([finding], "unsupported", language, "unknown").body).toBe(
      `${text.summaryFoundBody} ${text.summaryUnidentifiedFoundNote}`,
    );
    expect(`${text.summaryUnidentifiedBody} ${text.summaryUnidentifiedFoundNote} ${text.findingsNoneUnidentified}`).not.toMatch(
      /this language|इस भाषा/i,
    );
    // Telugu, Urdu and Bengali keep the language-specific wording.
    for (const detected of ["te", "ur", "bn"] as const) {
      expect(summarizeResult([], "unsupported", language, detected).body).toBe(text.summaryUnsupportedBody);
      expect(summarizeResult([finding], "unsupported", language, detected).body).toContain(text.summaryUnsupportedFoundNote);
    }
    // The identified language makes no difference to supported or partial coverage.
    expect(summarizeResult([], "supported", language, "en").body).toBe(text.summaryNoneBody);
    expect(summarizeResult([], "partial", language, "mixed").body).toBe(text.summaryPartialBody);
  }
});

// Partly checked messages: a mix of scripts, Hindi, and Hindi in English letters. The summary
// follows the coverage value the API reports, not the name of the language.
const PARTLY_CHECKED = [
  ["mixed", mixedNoFindings as Fixture],
  ["hi", hindiBenign as Fixture],
  ["hi-Latn", romanisedHindiBenign as Fixture],
] as const;

describe.each(PARTLY_CHECKED)("a partly checked message with no findings (%s)", (detected, fixture) => {
  test.each(["en", "hi"] as const)("is not given the ordinary no-warning-signs summary (%s results)", async (language) => {
    expect(fixture.response.findings).toEqual([]);
    expect(fixture.response.language.detected).toBe(detected);
    expect(fixture.response.language.coverage).toBe("partial");
    const { user } = await analyze(fixture);
    if (language === "hi") await user.selectOptions(selector(), "hi");
    const text = RESULTS_TEXT[language];

    expect(headings(2)).toEqual([text.summaryUnsupportedTitle]);
    expect(within(results()).getByText(text.summaryPartialBody)).toBeInTheDocument();
    expect(within(results()).queryByText(text.summaryNoneTitle)).toBeNull();
    expect(results().textContent).toMatch(/This does not mean the message is safe|इसका मतलब यह नहीं है कि संदेश सुरक्षित है/);
    // Still partial, never relabelled as unsupported or fully supported.
    expect(within(results()).getByText(text.coverageLabels.partial)).toBeInTheDocument();
    expect(within(results()).queryByText(text.coverageLabels.unsupported)).toBeNull();
    expect(within(results()).queryByText(text.coverageLabels.supported)).toBeNull();
    expect(within(results()).queryByText(text.summaryUnsupportedBody)).toBeNull();
    expect(within(results()).queryByText(text.findingsNoneUnsupported)).toBeNull();
    // The note under "Warning signs" is qualified too, not the standalone "none appeared".
    expect(within(results()).getByText(text.findingsNonePartial)).toBeInTheDocument();
    expect(within(results()).queryByText(text.findingsNone)).toBeNull();
    expect(results().textContent).not.toMatch(/None of the warning signs we check for appeared|उनमें से कोई इस संदेश में नहीं मिला/);
    expect(within(results()).getByText(text.languageLabels[detected])).toBeInTheDocument();
    expect(within(results()).getByText(localizeApiText(fixture.response.language.notice, language))).toBeInTheDocument();
    expect(results().querySelector(".submitted__text")?.textContent).toBe(fixture.message);
  });
});

test.each(["en", "hi"] as const)("fully checked English with no findings keeps the ordinary summary (%s results)", async (language) => {
  const fixture = benign as Fixture;
  expect(fixture.response.findings).toEqual([]);
  expect(fixture.response.language.coverage).toBe("supported");
  const { user } = await analyze(fixture);
  if (language === "hi") await user.selectOptions(selector(), "hi");
  const text = RESULTS_TEXT[language];

  expect(headings(2)).toEqual([text.summaryNoneTitle]);
  expect(within(results()).getByText(text.summaryNoneBody)).toBeInTheDocument();
  expect(within(results()).getByText(text.findingsNone)).toBeInTheDocument();
  expect(within(results()).getByText(text.coverageLabels.supported)).toBeInTheDocument();
  expect(within(results()).queryByText(text.summaryUnsupportedTitle)).toBeNull();
  expect(results().textContent).toMatch(/does not mean the message is safe|इसका मतलब यह नहीं है कि संदेश सुरक्षित है/);
});

test.each([
  ["Hindi", hindiScam as Fixture],
  ["Romanized Hindi", romanisedHindiScam as Fixture],
])("the classifier stays unavailable and unobtrusive for %s, in either results language", async (_name, fixture) => {
  const { user } = await analyze(fixture);
  const card = () => screen.getByRole("heading", { level: 3, name: /Auxiliary signal|सहायक संकेत/ }).closest("section") as HTMLElement;

  expect(fixture.response.classifier.status).toBe("not_applicable");
  expect(within(card()).getByText("Not applied to this message")).toBeInTheDocument();
  await user.selectOptions(selector(), "hi");
  expect(within(card()).getByText("इस संदेश पर लागू नहीं किया गया")).toBeInTheDocument();
  expect(within(card()).getByText("प्रायोगिक")).toBeInTheDocument();
  // Never a score, gauge or verdict, and always the last section before the button.
  expect(card().textContent).not.toMatch(/%|score|confidence|स्कोर|प्रतिशत|धोखाधड़ी है।$/i);
  expect(card().querySelector("meter, progress")).toBeNull();
  expect(headings(3).at(-1)).toBe("सहायक संकेत");
});

// --- "What happened next?" in Hindi ----------------------------------------------------------

test("next steps follow the results language, with the same order, sources and helpline link", async () => {
  const { user, fetchMock } = await analyze(englishScam as Fixture, nextSteps);
  await user.selectOptions(selector(), "hi");
  await user.click(within(results()).getByRole("button", { name: "बताएँ कि क्या हुआ" }));

  const hindi = RESULTS_TEXT.hi;
  const radios = await within(results()).findAllByRole("radio");
  expect(radios.map((radio) => radio.closest("label")?.textContent)).toEqual(
    nextSteps.situations.map((situation) => hindi.situationLabels[situation.id as keyof typeof hindi.situationLabels]),
  );

  await user.click(within(results()).getByRole("radio", { name: hindi.situationLabels.lost_money }));
  const section = within(results()).getByRole("heading", { level: 3, name: "आगे क्या हुआ?" }).closest("section") as HTMLElement;
  const cards = within(section).getAllByRole("listitem");
  expect(cards.map((card) => within(card).getByRole("heading", { level: 4 }).textContent)).toEqual([
    "साइबर अपराध की शिकायत",
    "फ़िशिंग: अगर आप जवाब दे चुके हैं",
  ]);
  expect(within(cards[0]).getByRole("link", { name: "1930 पर कॉल करें" })).toHaveAttribute("href", "tel:1930");
  expect(within(cards[0]).getByRole("link", { name: /आधिकारिक स्रोत देखें/ })).toHaveAttribute("href", "https://i4c.mha.gov.in/");
  expect(within(cards[0]).getByText(nextSteps.situations[3].steps[0].source.publisher)).toBeInTheDocument();
  expect(within(cards[1]).queryByRole("link", { name: /कॉल/ })).toBeNull();
  expect(within(section).getByText(API_TEXT_HINDI[nextSteps.notice])).toBeInTheDocument();

  // Back to English: same choice, same steps, English wording, and no further request.
  await user.selectOptions(selector(), "en");
  expect(within(results()).getByRole("radio", { name: "I paid, or money has left my account" })).toBeChecked();
  expect(within(results()).getByRole("link", { name: "Call 1930" })).toHaveAttribute("href", "tel:1930");
  expect(fetchMock).toHaveBeenCalledTimes(2);
  expect(fetchMock.mock.calls[1][0]).toBe("/next-steps");
  expect(fetchMock.mock.calls[1][1].body).toBeUndefined();
});
