import { useCallback, useEffect, useReducer, useRef, useState } from "react";
import { AnalyzeError, analyzeMessage, type ApiErrorKind } from "./api/client";
import { MAX_MESSAGE_LENGTH, type AnalyzeResponse } from "./api/types";
import { Analyzer, type InputProblem } from "./components/Analyzer";
import { Header } from "./components/Header";
import { Hero } from "./components/Hero";
import { Results } from "./components/Results";
import { About, AnalyzingState, ErrorState, Footer, HowItWorks, SafetyTips } from "./components/Sections";
import { useResultsLanguage } from "./lib/resultsLanguage";
import { countCharacters } from "./lib/text";

export const SLOW_AFTER_MS = 8000;

type Phase =
  | { kind: "idle" }
  | { kind: "analyzing"; slow: boolean }
  | { kind: "result"; message: string; data: AnalyzeResponse }
  | { kind: "error"; error: ApiErrorKind };

type Action =
  | { type: "start" }
  | { type: "slow" }
  | { type: "success"; message: string; data: AnalyzeResponse }
  | { type: "failure"; error: ApiErrorKind }
  | { type: "reset" };

function reducer(phase: Phase, action: Action): Phase {
  switch (action.type) {
    case "start":
      return { kind: "analyzing", slow: false };
    case "slow":
      return phase.kind === "analyzing" ? { ...phase, slow: true } : phase;
    case "success":
      return { kind: "result", message: action.message, data: action.data };
    case "failure":
      return { kind: "error", error: action.error };
    case "reset":
      return { kind: "idle" };
  }
}

function inputProblem(text: string): InputProblem {
  if (!text.trim()) return "blank";
  if (countCharacters(text) > MAX_MESSAGE_LENGTH) return "too_long";
  return null;
}

export default function App() {
  const [phase, dispatch] = useReducer(reducer, { kind: "idle" });
  const [text, setText] = useState("");
  const [problem, setProblem] = useState<InputProblem>(null);
  // How results are presented. It is never sent to the API and does not change the analysis.
  const [resultsLanguage, setResultsLanguage] = useResultsLanguage();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const resultsHeadingRef = useRef<HTMLHeadingElement>(null);
  const requestRef = useRef<AbortController | null>(null);

  useEffect(() => () => requestRef.current?.abort(), []);

  // Bring the result summary into view and move focus to it, so keyboard and screen-reader
  // users land on it. Scrolling is instant when the user has asked for reduced motion.
  useEffect(() => {
    if (phase.kind !== "result") return;
    const heading = resultsHeadingRef.current;
    if (!heading) return;
    const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
    heading.focus({ preventScroll: true });
    heading.scrollIntoView?.({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
  }, [phase]);

  const focusInput = useCallback(() => {
    document.getElementById("analyze")?.scrollIntoView({ behavior: "smooth", block: "start" });
    textareaRef.current?.focus({ preventScroll: true });
  }, []);

  const analyze = useCallback(async () => {
    const found = inputProblem(text);
    setProblem(found);
    if (found) {
      textareaRef.current?.focus();
      return;
    }
    requestRef.current?.abort();
    const controller = new AbortController();
    requestRef.current = controller;
    dispatch({ type: "start" });
    const slowTimer = window.setTimeout(() => dispatch({ type: "slow" }), SLOW_AFTER_MS);
    try {
      const data = await analyzeMessage(text, { signal: controller.signal });
      dispatch({ type: "success", message: text, data });
    } catch (error) {
      if (controller.signal.aborted) return;
      dispatch({ type: "failure", error: error instanceof AnalyzeError ? error.kind : "network" });
    } finally {
      window.clearTimeout(slowTimer);
    }
  }, [text]);

  const clear = useCallback(() => {
    requestRef.current?.abort();
    setText("");
    setProblem(null);
    dispatch({ type: "reset" });
    textareaRef.current?.focus();
  }, []);

  const changeText = useCallback(
    (value: string) => {
      setText(value);
      if (problem) setProblem(null);
    },
    [problem],
  );

  return (
    <>
      <a className="skip-link" href="#analyze" onClick={focusInput}>
        Skip to the message checker
      </a>
      <Header onStart={focusInput} />
      <main id="top">
        <Hero />
        <Analyzer
          value={text}
          onChange={changeText}
          onSubmit={analyze}
          onClear={clear}
          busy={phase.kind === "analyzing"}
          problem={problem}
          textareaRef={textareaRef}
          resultsLanguage={resultsLanguage}
          onResultsLanguageChange={setResultsLanguage}
        />
        {phase.kind === "analyzing" && <AnalyzingState slow={phase.slow} />}
        {phase.kind === "error" && <ErrorState kind={phase.error} onRetry={analyze} />}
        {phase.kind === "result" && (
          <Results
            ref={resultsHeadingRef}
            message={phase.message}
            data={phase.data}
            language={resultsLanguage}
            onLanguageChange={setResultsLanguage}
            onCheckAnother={clear}
          />
        )}
        <HowItWorks />
        <SafetyTips />
        <About />
      </main>
      <Footer />
    </>
  );
}
