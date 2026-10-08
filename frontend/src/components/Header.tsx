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
