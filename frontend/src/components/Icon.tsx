// Small inline icon set. Icons are decorative unless a label is given.

const PATHS = {
  shieldCheck: ["M12 3l7 3v5c0 4.6-3 8.4-7 10-4-1.6-7-5.4-7-10V6l7-3z", "M9 12l2 2 4-4"],
  lock: ["M7 11V8a5 5 0 0110 0v3", "M6 11h12a1 1 0 011 1v8a1 1 0 01-1 1H6a1 1 0 01-1-1v-8a1 1 0 011-1z"],
  check: ["M5 12.5l4.5 4.5L19 7.5"],
  message: ["M20 12a8 8 0 01-11.6 7.1L4 20l1-4.4A8 8 0 1120 12z"],
  search: ["M11 18a7 7 0 100-14 7 7 0 000 14z", "M20 20l-4.2-4.2"],
  monitor: ["M4 5h16a1 1 0 011 1v9a1 1 0 01-1 1H4a1 1 0 01-1-1V6a1 1 0 011-1z", "M9 20h6", "M12 16v4"],
  sun: ["M12 16a4 4 0 100-8 4 4 0 000 8z", "M12 2v2", "M12 20v2", "M4.9 4.9l1.4 1.4", "M17.7 17.7l1.4 1.4", "M2 12h2", "M20 12h2", "M4.9 19.1l1.4-1.4", "M17.7 6.3l1.4-1.4"],
  moon: ["M20 14.5A8 8 0 019.5 4a8 8 0 1010.5 10.5z"],
  upload: ["M12 15V4", "M7.5 8.5L12 4l4.5 4.5", "M5 15v4a1 1 0 001 1h12a1 1 0 001-1v-4"],
  sparkle: ["M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z", "M19 16l.8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8z"],
  alert: ["M12 4L2.8 20h18.4L12 4z", "M12 10v4.5", "M12 17.5h.01"],
  info: ["M12 21a9 9 0 100-18 9 9 0 000 18z", "M12 11v5", "M12 8h.01"],
  external: ["M14 4h6v6", "M20 4l-9 9", "M18 14v5a1 1 0 01-1 1H5a1 1 0 01-1-1V7a1 1 0 011-1h5"],
  globe: ["M12 21a9 9 0 100-18 9 9 0 000 18z", "M3 12h18", "M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9s1.3-6.4 3.8-9z"],
  menu: ["M4 7h16", "M4 12h16", "M4 17h16"],
  close: ["M6 6l12 12", "M18 6L6 18"],
  chevronDown: ["M6 9l6 6 6-6"],
  arrowRight: ["M5 12h14", "M13 6l6 6-6 6"],
  refresh: ["M20 12a8 8 0 11-2.3-5.7", "M20 4v4.5h-4.5"],
  book: ["M5 4h9a3 3 0 013 3v13H8a3 3 0 01-3-3V4z", "M5 17a3 3 0 013-3h9"],
  phone: ["M8 3h8a1 1 0 011 1v16a1 1 0 01-1 1H8a1 1 0 01-1-1V4a1 1 0 011-1z", "M11 18h2"],
} as const;

export type IconName = keyof typeof PATHS;

interface IconProps {
  name: IconName;
  size?: number;
  label?: string;
  className?: string;
}

export function Icon({ name, size = 20, label, className }: IconProps) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      focusable="false"
    >
      {PATHS[name].map((d) => (
        <path key={d} d={d} />
      ))}
    </svg>
  );
}
