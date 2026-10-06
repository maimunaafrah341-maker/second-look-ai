import { forwardRef, type ReactNode } from "react";
import type { AnalyzeResponse, ClassifierSection, Finding, GuidanceMatch, LanguageSection } from "../api/types";
import { SAFETY_STEPS, SAFETY_STEPS_SOURCE } from "../content/copy";
import { summarizeResult } from "../lib/status";
import { categoryLabel, COVERAGE_LABELS, formatDate, highlightEvidence, LANGUAGE_LABELS } from "../lib/text";
import { Icon } from "./Icon";

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

function SubmittedMessage({ message, findings, language }: { message: string; findings: Finding[]; language: LanguageSection }) {
  const parts = highlightEvidence(
    message,
    findings.map((finding) => finding.evidence),
  );
  return (
    <div className="submitted card card--muted">
      <div className="submitted__head">
        <h3 className="submitted__title">Your message</h3>
        <p className="language-chip">
          <span>
            <Icon name="globe" size={15} />
            Message language (estimate): <strong>{LANGUAGE_LABELS[language.detected] ?? language.detected}</strong>
          </span>
          <span className={`coverage coverage--${language.coverage}`}>{COVERAGE_LABELS[language.coverage] ?? language.coverage}</span>
        </p>
      </div>
      <p className="submitted__text" dir="auto">
        {parts.map((part, index) =>
          part.highlighted ? (
            <mark key={index}>{part.text}</mark>
          ) : (
            <span key={index}>{part.text}</span>
          ),
        )}
      </p>
      <p className="submitted__note">{language.notice}</p>
    </div>
  );
}

function WarningSignCard({ finding }: { finding: Finding }) {
  return (
    <li className="finding card">
      <div className="finding__head">
        <span className="finding__icon">
          <Icon name="alert" size={18} />
        </span>
        <h4 className="finding__title">{categoryLabel(finding.category)}</h4>
      </div>
      <figure className="finding__evidence">
        <figcaption>From your message</figcaption>
        <blockquote dir="auto">“{finding.evidence}”</blockquote>
      </figure>
      <p className="finding__why">
        <strong>Why it matters: </strong>
        {finding.explanation}
      </p>
    </li>
  );
}

function GuidanceCard({ match }: { match: GuidanceMatch }) {
  const { source } = match;
  return (
    <li className="guidance card">
      <p className="guidance__publisher">
        <Icon name="book" size={16} />
        {source.publisher}
      </p>
      <h4 className="guidance__topic">{match.topic}</h4>
      <p className="guidance__summary">{match.summary}</p>
      <p className="guidance__note">{match.summary_note}</p>
      <dl className="guidance__meta">
        <div>
          <dt>Source</dt>
          <dd>{source.title}</dd>
        </div>
        <div>
          <dt>Section</dt>
          <dd>{source.section}</dd>
        </div>
        {source.published && (
          <div>
            <dt>Published</dt>
            <dd>{formatDate(source.published)}</dd>
          </div>
        )}
        <div>
          <dt>Retrieved</dt>
          <dd>{formatDate(source.retrieved)}</dd>
        </div>
      </dl>
      <a className="guidance__link" href={source.url} target="_blank" rel="noopener noreferrer">
        View official source
        <Icon name="external" size={15} />
        <span className="visually-hidden"> (opens in a new tab)</span>
      </a>
    </li>
  );
}

const CLASSIFIER_HEADLINES: Record<string, string> = {
  spam_like: "Resembles older English SMS spam",
  not_spam_like: "Does not resemble older English SMS spam",
  not_applicable: "Not applied to this message",
  unavailable: "Not available right now",
};

function ClassifierSignal({ classifier }: { classifier: ClassifierSection }) {
  const key = classifier.status === "ok" && classifier.label ? classifier.label : classifier.status;
  return (
    <section className="result-section result-section--quiet" aria-labelledby="classifier-title">
      <div className="classifier card card--muted">
        <div className="classifier__head">
          <h3 id="classifier-title" className="classifier__title">
            Auxiliary signal
          </h3>
          <span className="pill pill--neutral">Experimental</span>
        </div>
        <p className="classifier__headline">{CLASSIFIER_HEADLINES[key] ?? "No signal"}</p>
        <p className="classifier__notice">{classifier.notice}</p>
        {classifier.model && (
          <p className="classifier__model">
            Trained on: {classifier.model.training_data}. It does not decide whether a message is fraudulent.
          </p>
        )}
      </div>
    </section>
  );
}

interface ResultsProps {
  message: string;
  data: AnalyzeResponse;
  onCheckAnother: () => void;
}

export const Results = forwardRef<HTMLHeadingElement, ResultsProps>(function Results({ message, data, onCheckAnother }, headingRef) {
  const summary = summarizeResult(data.findings);
  return (
    <section className="results" aria-labelledby="results-title">
      <div className="container results__inner">
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

        <SubmittedMessage message={message} findings={data.findings} language={data.language} />

        <section className="result-section" aria-labelledby="findings-title">
          <SectionHeading id="findings-title" step="1 · What we noticed" title="Warning signs">
            Specific phrases from your message, and why they deserve attention.
          </SectionHeading>
          {data.findings.length > 0 ? (
            <ul className="finding-list">
              {data.findings.map((finding) => (
                <WarningSignCard key={finding.category} finding={finding} />
              ))}
            </ul>
          ) : (
            <p className="empty-note card card--muted">None of the warning signs we check for appeared in this message.</p>
          )}
          <p className="section-notice">
            <Icon name="info" size={15} />
            {data.notice}
          </p>
        </section>

        <section className="result-section" aria-labelledby="guidance-title">
          <SectionHeading id="guidance-title" step="2 · Official guidance" title="What official sources say">
            Matched from a small collection of Indian government cyber-safety guidance.
          </SectionHeading>
          {data.guidance.matches.length > 0 && (
            <ul className="guidance-list">
              {data.guidance.matches.map((match) => (
                <GuidanceCard key={`${match.source.url}#${match.topic}`} match={match} />
              ))}
            </ul>
          )}
          <p className={data.guidance.matches.length > 0 ? "section-notice" : "empty-note card card--muted"}>
            <Icon name="info" size={15} />
            {data.guidance.notice}
          </p>
        </section>

        <section className="result-section" aria-labelledby="steps-title">
          <SectionHeading id="steps-title" step="3 · What to do next" title="Safer next steps">
            General steps for any suspicious message. They are the same for every check.
          </SectionHeading>
          <ol className="steps">
            {SAFETY_STEPS.map((step, index) => (
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
          <p className="section-notice">{SAFETY_STEPS_SOURCE}</p>
        </section>

        <ClassifierSignal classifier={data.classifier} />

        <div className="results__again">
          <button type="button" className="button button--secondary" onClick={onCheckAnother}>
            <Icon name="refresh" size={18} />
            Check another message
          </button>
        </div>
      </div>
    </section>
  );
});
