import { Icon } from "./Icon";

const TRUST_POINTS = [
  { icon: "shieldCheck" as const, label: "Evidence-led" },
  { icon: "lock" as const, label: "You control what you share" },
  { icon: "check" as const, label: "Clear next steps" },
];

export function Hero() {
  return (
    <section className="hero" aria-labelledby="hero-title">
      <div className="container hero__inner">
        <div className="hero__copy">
          <p className="eyebrow eyebrow--rule">Digital safety</p>
          <h1 id="hero-title" className="hero__title">
            <span>Pause. Check.</span>
            <span className="hero__title-second">Know what to do next.</span>
          </h1>
          <p className="hero__lead">
            Second Look helps you understand suspicious messages by highlighting warning signs, connecting them to
            official guidance, and showing safer next steps.
          </p>
          <ul className="trust-points">
            {TRUST_POINTS.map((point) => (
              <li key={point.label}>
                <Icon name={point.icon} size={18} />
                {point.label}
              </li>
            ))}
          </ul>
        </div>

        <div className="hero__art" aria-hidden="true">
          <div className="hero__orbit" />
          <div className="hero__card">
            <div className="hero__dots">
              <span />
              <span />
            </div>
            <div className="hero__line hero__line--long" />
            <div className="hero__line" />
            <div className="hero__line hero__line--short" />
            <div className="hero__flag">
              <Icon name="alert" size={16} />
              Review this request
            </div>
          </div>
          <div className="hero__badge">
            <Icon name="shieldCheck" size={16} />
            Evidence first
          </div>
          <div className="hero__seal">
            <Icon name="search" size={30} />
            <span>Second look</span>
          </div>
        </div>
      </div>
    </section>
  );
}
