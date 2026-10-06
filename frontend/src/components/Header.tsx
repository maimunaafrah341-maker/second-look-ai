import { useEffect, useId, useState } from "react";
import { useTheme, type ThemePreference } from "../lib/theme";
import { Icon, type IconName } from "./Icon";

const NAV_LINKS = [
  { href: "#how-it-works", label: "How it works" },
  { href: "#safety-tips", label: "Safety tips" },
  { href: "#about", label: "About" },
];

const THEME_OPTIONS: { value: ThemePreference; label: string; icon: IconName }[] = [
  { value: "system", label: "System theme", icon: "monitor" },
  { value: "light", label: "Light theme", icon: "sun" },
  { value: "dark", label: "Dark theme", icon: "moon" },
];

/** Interface languages. Only English is available; the others are listed as planned. */
const INTERFACE_LANGUAGES = [
  { value: "en", label: "English", available: true },
  { value: "hi", label: "हिन्दी", available: false },
  { value: "te", label: "తెలుగు", available: false },
  { value: "ur", label: "اردو", available: false },
  { value: "bn", label: "বাংলা", available: false },
];

export function ThemeSwitch() {
  const { preference, setPreference } = useTheme();
  return (
    <div className="theme-switch" role="group" aria-label="Theme">
      {THEME_OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          className="theme-switch__option"
          aria-pressed={preference === option.value}
          aria-label={option.label}
          title={option.label}
          onClick={() => setPreference(option.value)}
        >
          <Icon name={option.icon} size={17} />
        </button>
      ))}
    </div>
  );
}

function InterfaceLanguage() {
  const id = useId();
  return (
    <div className="ui-language">
      <label htmlFor={id} className="visually-hidden">
        Interface language (this does not change which message languages can be checked)
      </label>
      <Icon name="globe" size={16} className="ui-language__icon" />
      <select
        id={id}
        className="ui-language__select"
        defaultValue="en"
        title="Interface language. The language of your message is estimated separately when you analyze it."
      >
        {INTERFACE_LANGUAGES.map((language) => (
          <option key={language.value} value={language.value} disabled={!language.available}>
            {language.available ? language.label : `${language.label} (coming soon)`}
          </option>
        ))}
      </select>
    </div>
  );
}

interface HeaderProps {
  onStart: () => void;
}

export function Header({ onStart }: HeaderProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuId = useId();

  useEffect(() => {
    if (!menuOpen) return;
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && setMenuOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [menuOpen]);

  return (
    <header className="site-header">
      <div className="container site-header__inner">
        <a href="#top" className="wordmark" aria-label="Second Look, home">
          Second <span>Look</span>
        </a>

        <button
          type="button"
          className="menu-toggle"
          aria-expanded={menuOpen}
          aria-controls={menuId}
          onClick={() => setMenuOpen((open) => !open)}
        >
          <Icon name={menuOpen ? "close" : "menu"} size={20} />
          <span className="visually-hidden">{menuOpen ? "Close menu" : "Open menu"}</span>
        </button>

        <div id={menuId} className={`site-header__menu${menuOpen ? " is-open" : ""}`}>
          <nav aria-label="Main">
            <ul className="site-nav">
              {NAV_LINKS.map((link) => (
                <li key={link.href}>
                  <a href={link.href} onClick={() => setMenuOpen(false)}>
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
          <div className="site-header__controls">
            <InterfaceLanguage />
            <ThemeSwitch />
            <button
              type="button"
              className="button button--primary button--compact"
              onClick={() => {
                setMenuOpen(false);
                onStart();
              }}
            >
              Try Second Look
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
