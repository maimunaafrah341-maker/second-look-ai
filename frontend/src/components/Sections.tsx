import { SAFETY_STEPS, SAFETY_STEPS_SOURCE } from "../content/copy";
import type { ApiErrorKind } from "../api/client";
import { Icon, type IconName } from "./Icon";

const HOW_IT_WORKS: { icon: IconName; title: string; text: string }[] = [
  {
    icon: "message",
    title: "Submit",
    text: "Paste the message you received. You stay in control of what you share. Screenshot upload is coming soon.",
  },
  {
    icon: "search",
    title: "Understand",
    text: "See the specific phrases and requests that may signal risk, explained in plain language.",
  },
  {
    icon: "shieldCheck",
    title: "Act",
    text: "Compare official guidance from Indian government sources and follow practical steps before you respond.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="page-section" aria-labelledby="how-title">
      <div className="container">
        <p className="eyebrow">A calmer way to check</p>
        <h2 id="how-title" className="section-title">
          Evidence, not fear.
        </h2>
        <p className="section-lead">Understand what deserves attention, why it matters, and the next safe action.</p>
        <ol className="how-grid">
          {HOW_IT_WORKS.map((item, index) => (
            <li key={item.title} className="how-card card">
              <div className="how-card__top">
                <span className="how-card__number">{String(index + 1).padStart(2, "0")}</span>
                <span className="icon-tile">
                  <Icon name={item.icon} size={20} />
                </span>
              </div>
              <h3 className="how-card__title">{item.title}</h3>
              <p className="how-card__text">{item.text}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

export function SafetyTips() {
  return (
    <section id="safety-tips" className="page-section page-section--alt" aria-labelledby="tips-title">
      <div className="container">
        <p className="eyebrow">Safety tips</p>
        <h2 id="tips-title" className="section-title">
          Before you reply, click, or pay
        </h2>
        <ul className="tips-grid">
          {SAFETY_STEPS.map((step) => (
            <li key={step.title} className="tip card">
              <h3 className="tip__title">{step.title}</h3>
              <p className="tip__text">{step.detail}</p>
            </li>
          ))}
        </ul>
        <p className="section-notice">{SAFETY_STEPS_SOURCE}</p>
      </div>
    </section>
  );
}

export function About() {
  return (
    <section id="about" className="page-section" aria-labelledby="about-title">
      <div className="container about">
        <div>
          <p className="eyebrow">About</p>
          <h2 id="about-title" className="section-title">
            What Second Look does, and what it doesn't
          </h2>
        </div>
        <div className="about__body">
          <p>
            Second Look checks a message for common warning signs, such as urgency, requests for an OTP or PIN,
            links, and payment demands, and quotes the exact words that triggered each one.
          </p>
          <p>
            It then looks for matching advice in a small collection of official Indian cyber-safety guidance from
            CERT-In and the Indian Cybercrime Coordination Centre, and links to the original documents.
          </p>
          <p>
            An experimental machine-learning signal is shown last. It was trained on older English SMS spam, so it
            is only applied to messages that appear to be in English, and it never decides whether a message is a
            scam.
          </p>
          <p>
            Checks are designed for English, with partial support for Hindi in Devanagari and in English letters.
            Second Look cannot tell you that a message is safe. When in doubt, contact the organisation through an
            official channel.
          </p>
        </div>
      </div>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="site-footer">
      <div className="container site-footer__inner">
        <span className="wordmark wordmark--small">
          Second <span>Look</span>
        </span>
        <p className="site-footer__tagline">Pause. Check. Know what to do next.</p>
        <p className="site-footer__note">Guidance, not a safety guarantee.</p>
      </div>
    </footer>
  );
}

const ERROR_TEXT: Record<ApiErrorKind, { title: string; body: string }> = {
  blank: { title: "There's no message to check", body: "Paste or type a message, then try again." },
  too_long: { title: "This message is too long", body: "Messages can be up to 5,000 characters. Shorten it and try again." },
  invalid: { title: "We couldn't read that request", body: "Please try again." },
  network: {
    title: "We couldn't reach Second Look",
    body: "Check your internet connection and try again. If the service was idle, it may take a moment to start.",
  },
  timeout: { title: "This is taking too long", body: "The service didn't respond in time. Please try again." },
  server: { title: "Something went wrong on our side", body: "Your message wasn't checked. Please try again in a moment." },
};

export function ErrorState({ kind, onRetry }: { kind: ApiErrorKind; onRetry: () => void }) {
  const text = ERROR_TEXT[kind];
  return (
    <section className="results" aria-live="assertive">
      <div className="container">
        <div className="state card state--error" role="alert">
          <span className="state__icon">
            <Icon name="alert" size={22} />
          </span>
          <div>
            <h2 className="state__title">{text.title}</h2>
            <p className="state__body">{text.body}</p>
            <button type="button" className="button button--secondary button--compact" onClick={onRetry}>
              <Icon name="refresh" size={16} />
              Try again
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}

export function AnalyzingState({ slow }: { slow: boolean }) {
  return (
    <section className="results" aria-live="polite" aria-busy="true">
      <div className="container">
        <div className="state card" role="status">
          <span className="spinner spinner--large" aria-hidden="true" />
          <div>
            <h2 className="state__title">Checking your message…</h2>
            <p className="state__body">
              {slow
                ? "The service is starting up. The first check after a quiet period can take up to a minute."
                : "Looking for warning signs and matching official guidance."}
            </p>
          </div>
        </div>
        <div className="skeleton" aria-hidden="true">
          <div className="skeleton__block" />
          <div className="skeleton__block skeleton__block--short" />
        </div>
      </div>
    </section>
  );
}
