import { forwardRef, useEffect, useId, useRef, useState, type ReactNode } from "react";
import { fetchNextSteps } from "../api/client";
import type {
  AnalyzeResponse,
  ClassifierSection,
  Finding,
  GuidanceMatch,
  LanguageSection,
  NextStepsResponse,
  StepAction,
} from "../api/types";
import { isLocalized, localizeApiText, localizeExplanation } from "../content/apiHindi";
import {
  HINDI_EXPLANATION_LABEL,
  HINDI_PRESENTATION_NOTE,
  ORIGINAL_ENGLISH_SUMMARY_LABEL,
  RESULTS_TEXT,
  type ResultsText,
} from "../content/resultsText";
import type { ResultsLanguage } from "../lib/resultsLanguage";
import { summarizeResult } from "../lib/status";
import { formatDate, highlightEvidence } from "../lib/text";
import { Icon } from "./Icon";
import { ResultsLanguageSelect } from "./ResultsLanguageSelect";

/** What every part of the results needs to present itself in the chosen language. */
interface Presentation {
  language: ResultsLanguage;
  text: ResultsText;
}

function SectionHeading({ id, step, title, children }: { id: string; step: string; title: string; children?: ReactNode }) {
  return (
    <div className="result-section__head">
      <p className="eyebrow">{step}</p>
      <h3 id={id} className="result-section__title">
        {title}
      </h3>
      {children && <p className="result-section__lead">{children}</p>}
    </div>
  );
}

interface SubmittedMessageProps extends Presentation {
  message: string;
  findings: Finding[];
  detected: LanguageSection;
}

function SubmittedMessage({ message, findings, detected, language, text }: SubmittedMessageProps) {
  const parts = highlightEvidence(
    message,
    findings.map((finding) => finding.evidence),
  );
  return (
    <div className="submitted card card--muted">
      <div className="submitted__head">
        <h3 className="submitted__title">{text.yourMessage}</h3>
        <p className="language-chip">
          <span>
            <Icon name="globe" size={15} />
            {text.messageLanguage} <strong>{text.languageLabels[detected.detected] ?? detected.detected}</strong>
          </span>
          <span className={`coverage coverage--${detected.coverage}`}>
            {text.coverageLabels[detected.coverage] ?? detected.coverage}
          </span>
        </p>
      </div>
      {/* The person's own words: shown exactly as submitted, in whatever language they are in. */}
      <p className="submitted__text" dir="auto" lang="">
        {parts.map((part, index) =>
          part.highlighted ? (
            <mark key={index}>{part.text}</mark>
          ) : (
            <span key={index}>{part.text}</span>
          ),
        )}
      </p>
      <p className="submitted__note">{localizeApiText(detected.notice, language)}</p>
    </div>
  );
}

function WarningSignCard({ finding, language, text }: { finding: Finding } & Presentation) {
  return (
    <li className="finding card">
      <div className="finding__head">
        <span className="finding__icon">
          <Icon name="alert" size={18} />
        </span>
        <h4 className="finding__title">{text.categoryLabels[finding.category] ?? text.categoryFallback}</h4>
      </div>
      <figure className="finding__evidence">
        <figcaption>{text.fromYourMessage}</figcaption>
        {/* Evidence is always the exact excerpt from the message, never translated. */}
        <blockquote dir="auto" lang="">
          “{finding.evidence}”
        </blockquote>
      </figure>
      <p className="finding__why">
        <strong>{text.whyItMatters}</strong>
        {localizeExplanation(finding.explanation, language)}
      </p>
    </li>
  );
}

// Only a plain phone link from the API is ever turned into a button.
const PHONE_LINK = /^tel:\d{3,15}$/;

interface GuidanceCardProps extends Presentation {
  match: Pick<GuidanceMatch, "topic" | "summary" | "summary_note" | "source">;
  action?: StepAction | null;
}

function GuidanceCard({ match, action, language, text }: GuidanceCardProps) {
  const { source } = match;
  const translated = isLocalized(match.summary, language);
  return (
    <li className="guidance card">
      {/* Publisher, title, section, dates and link are the source's own and are never translated. */}
      <p className="guidance__publisher" lang="en">
        <Icon name="book" size={16} />
        {source.publisher}
      </p>
      <h4 className="guidance__topic">{localizeApiText(match.topic, language)}</h4>
      {translated && <p className="guidance__translation-label">{HINDI_EXPLANATION_LABEL}</p>}
      <p className="guidance__summary">{localizeApiText(match.summary, language)}</p>
      <p className="guidance__note">{localizeApiText(match.summary_note, language)}</p>
      {translated && (
        <details className="guidance__original">
          <summary>{ORIGINAL_ENGLISH_SUMMARY_LABEL}</summary>
          <p lang="en">
            <strong>{match.topic}.</strong> {match.summary}
          </p>
        </details>
      )}
      <dl className="guidance__meta">
        <div>
          <dt>{text.source}</dt>
          <dd lang="en">{source.title}</dd>
        </div>
        <div>
          <dt>{text.section}</dt>
          <dd lang="en">{source.section}</dd>
        </div>
        {source.published && (
          <div>
            <dt>{text.published}</dt>
            <dd lang="en">{formatDate(source.published)}</dd>
          </div>
        )}
        <div>
          <dt>{text.retrieved}</dt>
          <dd lang="en">{formatDate(source.retrieved)}</dd>
        </div>
      </dl>
      {action && PHONE_LINK.test(action.href) && (
        <a className="button button--primary button--compact guidance__action" href={action.href}>
          <Icon name="alert" size={16} />
          {localizeApiText(action.label, language)}
        </a>
      )}
      <a className="guidance__link" href={source.url} target="_blank" rel="noopener noreferrer">
        {text.viewSource}
        <Icon name="external" size={15} />
        <span className="visually-hidden">{text.opensInNewTab}</span>
      </a>
    </li>
  );
}

type NextStepsState = { status: "idle" | "loading" | "error" } | { status: "ready"; data: NextStepsResponse };

/**
 * "What happened next?": the person picks what happened and sees the matching steps from
 * the official guidance. The choice stays in the browser; it is never sent anywhere.
 */
function NextSteps({ language, text }: Presentation) {
  const [state, setState] = useState<NextStepsState>({ status: "idle" });
  const [selected, setSelected] = useState<string | null>(null);
  const groupName = useId();
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const load = async () => {
    setState({ status: "loading" });
    try {
      const data = await fetchNextSteps();
      if (mounted.current) setState({ status: "ready", data });
    } catch {
      if (mounted.current) setState({ status: "error" });
    }
  };

  const situation = state.status === "ready" ? state.data.situations.find((item) => item.id === selected) : undefined;

  return (
    <section className="result-section" aria-labelledby="next-title">
      <SectionHeading id="next-title" step={text.nextStep} title={text.nextTitle}>
        {text.nextLead}
      </SectionHeading>

      {state.status === "idle" && (
        <div>
          <button type="button" className="button button--secondary" onClick={load}>
            {text.nextChoose}
            <Icon name="chevronDown" size={16} />
          </button>
        </div>
      )}
      {state.status === "loading" && (
        <p className="empty-note card card--muted" role="status">
          <span className="spinner" aria-hidden="true" />
          {text.nextLoading}
        </p>
      )}
      {state.status === "error" && (
        <div className="empty-note card card--muted next-steps__error" role="alert">
          <p>{text.nextError}</p>
          <button type="button" className="button button--secondary button--compact" onClick={load}>
            <Icon name="refresh" size={16} />
            {text.tryAgain}
          </button>
        </div>
      )}
      {state.status === "ready" && (
        <>
          <fieldset className="next-steps__options">
            <legend className="visually-hidden">{text.nextTitle}</legend>
            {state.data.situations.map((item) => (
              <label key={item.id} className={`next-steps__option card${selected === item.id ? " is-selected" : ""}`}>
                <input
                  type="radio"
                  name={groupName}
                  value={item.id}
                  checked={selected === item.id}
                  onChange={() => setSelected(item.id)}
                />
                {/* Translated by the situation's id; an id without a translation keeps the API's label. */}
                <span>{text.situationLabels[item.id] ?? item.label}</span>
              </label>
            ))}
          </fieldset>
          <div aria-live="polite">
            {situation && (
              <div className="result-section">
                <ol className="guidance-list">
                  {situation.steps.map((step) => (
                    <GuidanceCard key={step.topic} match={step} action={step.action} language={language} text={text} />
                  ))}
                </ol>
                <p className="section-notice">
                  <Icon name="info" size={15} />
                  {localizeApiText(state.data.notice, language)}
                </p>
              </div>
            )}
          </div>
        </>
      )}
    </section>
  );
}

function ClassifierSignal({ classifier, language, text }: { classifier: ClassifierSection } & Presentation) {
  const key = classifier.status === "ok" && classifier.label ? classifier.label : classifier.status;
  return (
    <section className="result-section result-section--quiet" aria-labelledby="classifier-title">
      <div className="classifier card card--muted">
        <div className="classifier__head">
          <h3 id="classifier-title" className="classifier__title">
            {text.classifierTitle}
          </h3>
          <span className="pill pill--neutral">{text.experimental}</span>
        </div>
        <p className="classifier__headline">{text.classifierHeadlines[key] ?? text.classifierNoSignal}</p>
        <p className="classifier__notice">{localizeApiText(classifier.notice, language)}</p>
        {classifier.model && (
          <p className="classifier__model">{text.classifierModel(localizeApiText(classifier.model.training_data, language))}</p>
        )}
      </div>
    </section>
  );
}

interface ResultsProps {
  message: string;
  data: AnalyzeResponse;
  language: ResultsLanguage;
  onLanguageChange: (language: ResultsLanguage) => void;
  onCheckAnother: () => void;
}

export const Results = forwardRef<HTMLHeadingElement, ResultsProps>(function Results(
  { message, data, language, onLanguageChange, onCheckAnother },
  headingRef,
) {
  const text = RESULTS_TEXT[language];
  const presentation: Presentation = { language, text };
  const { coverage, detected } = data.language;
  const summary = summarizeResult(data.findings, coverage, language, detected);
  // The note shown when nothing was found, qualified by how much of the message could be checked.
  const findingsNone =
    coverage === "unsupported"
      ? detected === "unknown"
        ? text.findingsNoneUnidentified
        : text.findingsNoneUnsupported
      : coverage === "partial"
        ? text.findingsNonePartial
        : text.findingsNone;

  return (
    <section className="results" aria-labelledby="results-title">
      <div className="container results__inner">
        <div className="results__language">
          <ResultsLanguageSelect value={language} onChange={onLanguageChange} />
          {language === "hi" && (
            <p className="results__language-note" lang="hi">
              {HINDI_PRESENTATION_NOTE}
            </p>
          )}
        </div>

        {/* Everything below is presented in the chosen language. The analysis itself is the same. */}
        <div className="results__body" lang={language}>
          <div className={`summary card summary--${summary.tone}`}>
            <span className="summary__icon">
              <Icon name={summary.tone === "attention" ? "alert" : "info"} size={22} />
            </span>
            <div>
              <h2 id="results-title" className="summary__title" tabIndex={-1} ref={headingRef}>
                {summary.title}
              </h2>
              <p className="summary__body">{summary.body}</p>
            </div>
          </div>

          <SubmittedMessage message={message} findings={data.findings} detected={data.language} {...presentation} />

          <section className="result-section" aria-labelledby="findings-title">
            <SectionHeading id="findings-title" step={text.findingsStep} title={text.findingsTitle}>
              {text.findingsLead}
            </SectionHeading>
            {data.findings.length > 0 ? (
              <ul className="finding-list">
                {data.findings.map((finding) => (
                  <WarningSignCard key={finding.category} finding={finding} {...presentation} />
                ))}
              </ul>
            ) : (
              <p className="empty-note card card--muted">{findingsNone}</p>
            )}
            <p className="section-notice">
              <Icon name="info" size={15} />
              {localizeApiText(data.notice, language)}
            </p>
          </section>

          <section className="result-section" aria-labelledby="guidance-title">
            <SectionHeading id="guidance-title" step={text.guidanceStep} title={text.guidanceTitle}>
              {text.guidanceLead}
            </SectionHeading>
            {data.guidance.matches.length > 0 && (
              <ul className="guidance-list">
                {data.guidance.matches.map((match) => (
                  <GuidanceCard key={`${match.source.url}#${match.topic}`} match={match} {...presentation} />
                ))}
              </ul>
            )}
            <p className={data.guidance.matches.length > 0 ? "section-notice" : "empty-note card card--muted"}>
              <Icon name="info" size={15} />
              {localizeApiText(data.guidance.notice, language)}
            </p>
          </section>

          <section className="result-section" aria-labelledby="steps-title">
            <SectionHeading id="steps-title" step={text.stepsStep} title={text.stepsTitle}>
              {text.stepsLead}
            </SectionHeading>
            <ol className="steps">
              {text.safetySteps.map((step, index) => (
                <li key={step.title} className="steps__item card">
                  <span className="steps__number" aria-hidden="true">
                    {index + 1}
                  </span>
                  <div>
                    <h4 className="steps__title">{step.title}</h4>
                    <p className="steps__detail">{step.detail}</p>
                  </div>
                </li>
              ))}
            </ol>
            <p className="section-notice">{text.safetyStepsSource}</p>
          </section>

          <NextSteps {...presentation} />

          <ClassifierSignal classifier={data.classifier} {...presentation} />

          <div className="results__again">
            <button type="button" className="button button--secondary" onClick={onCheckAnother}>
              <Icon name="refresh" size={18} />
              {text.checkAnother}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
});
