import { useId, useRef, useState, type FormEvent, type Ref } from "react";
import { MAX_MESSAGE_LENGTH } from "../api/types";
import { EXAMPLE_MESSAGES } from "../content/copy";
import { countCharacters } from "../lib/text";
import { Icon } from "./Icon";

export type InputProblem = "blank" | "too_long" | null;

export const INPUT_PROBLEM_TEXT: Record<Exclude<InputProblem, null>, string> = {
  blank: "Paste or type a message to analyze.",
  too_long: `This message is longer than ${MAX_MESSAGE_LENGTH.toLocaleString("en-IN")} characters. Shorten it and try again.`,
};

interface AnalyzerProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onClear: () => void;
  busy: boolean;
  problem: InputProblem;
  textareaRef: Ref<HTMLTextAreaElement>;
}

export function Analyzer({ value, onChange, onSubmit, onClear, busy, problem, textareaRef }: AnalyzerProps) {
  const ids = { input: useId(), count: useId(), error: useId(), help: useId(), examples: useId(), upload: useId() };
  const [examplesOpen, setExamplesOpen] = useState(false);
  const examplesButton = useRef<HTMLButtonElement>(null);
  const count = countCharacters(value);
  const overLimit = count > MAX_MESSAGE_LENGTH;
  const describedBy = [ids.help, ids.count, problem ? ids.error : null].filter(Boolean).join(" ");

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!busy) onSubmit();
  };

  const chooseExample = (message: string) => {
    onChange(message);
    setExamplesOpen(false);
    examplesButton.current?.focus();
  };

  return (
    <section id="analyze" className="analyzer-section" aria-labelledby="analyzer-title">
      <div className="container">
        <form className="analyzer card" onSubmit={submit} noValidate>
          <div className="analyzer__head">
            <div>
              <p className="eyebrow">Start here</p>
              <h2 id="analyzer-title" className="analyzer__title">
                What did you receive?
              </h2>
            </div>
            <p className="analyzer__privacy">
              <Icon name="lock" size={15} />
              Sent only to analyze it. Not saved by the app.
            </p>
          </div>

          <label htmlFor={ids.input} className="visually-hidden">
            Message to check
          </label>
          <textarea
            id={ids.input}
            ref={textareaRef}
            className="analyzer__input"
            value={value}
            onChange={(event) => onChange(event.target.value)}
            placeholder="Paste a suspicious SMS, WhatsApp message, email, or other message here…"
            rows={6}
            readOnly={busy}
            aria-invalid={problem ? true : undefined}
            aria-describedby={describedBy}
            spellCheck={false}
          />
          <div className="analyzer__meta">
            <p id={ids.help} className="analyzer__help">
              Paste the text exactly as you received it. Checks are designed for English, with partial support for
              Hindi; other languages get only basic checks.
            </p>
            <p id={ids.count} className={`analyzer__count${overLimit ? " is-over" : ""}`} aria-live="polite">
              {count.toLocaleString("en-IN")} / {MAX_MESSAGE_LENGTH.toLocaleString("en-IN")}
              <span className="visually-hidden"> characters</span>
            </p>
          </div>

          {problem && (
            <p id={ids.error} className="field-error" role="alert">
              <Icon name="alert" size={16} />
              {INPUT_PROBLEM_TEXT[problem]}
            </p>
          )}

          <div className="analyzer__actions">
            <div className="analyzer__primary-actions">
              <button type="submit" className="button button--primary" disabled={busy} aria-busy={busy}>
                {busy ? <span className="spinner" aria-hidden="true" /> : <Icon name="sparkle" size={18} />}
                {busy ? "Analyzing…" : "Analyze message"}
              </button>
              <button type="button" className="button button--ghost" onClick={onClear} disabled={busy || value === ""}>
                Clear
              </button>
              <button
                type="button"
                className="button button--secondary"
                aria-disabled="true"
                aria-describedby={ids.upload}
                onClick={(event) => event.preventDefault()}
              >
                <Icon name="upload" size={18} />
                Upload screenshot
                <span className="pill">Coming soon</span>
              </button>
              <span id={ids.upload} className="visually-hidden">
                Screenshot checking is not available yet. Copy the message text and paste it instead.
              </span>
            </div>

            <div className="examples">
              <button
                ref={examplesButton}
                type="button"
                className="link-button"
                aria-expanded={examplesOpen}
                aria-controls={ids.examples}
                onClick={() => setExamplesOpen((open) => !open)}
                disabled={busy}
              >
                Try an example
                <Icon name="chevronDown" size={16} className={examplesOpen ? "is-flipped" : undefined} />
              </button>
              {examplesOpen && (
                <ul id={ids.examples} className="examples__list" aria-label="Example messages (written for this demo)">
                  {EXAMPLE_MESSAGES.map((example) => (
                    <li key={example.id}>
                      <button type="button" onClick={() => chooseExample(example.message)}>
                        {example.label}
                      </button>
                    </li>
                  ))}
                  <li className="examples__note">Examples are written for this demo, not real messages.</li>
                </ul>
              )}
            </div>
          </div>

          <p className="analyzer__disclaimer">
            <Icon name="info" size={15} />
            Second Look offers guidance, not a guarantee. When in doubt, verify through an official channel.
          </p>
        </form>
      </div>
    </section>
  );
}
