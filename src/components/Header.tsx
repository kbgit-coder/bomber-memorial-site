"use client";

import { useState } from "react";
import Link from "next/link";

function trackNav(destination: string) {
  (window as { posthog?: { capture: (e: string, p?: Record<string, unknown>) => void } }).posthog?.capture("nav_click", { destination });
}

const NAV_LINKS = [
  { href: "/", label: "Home", destination: "home" },
  { href: "/region/united-kingdom", label: "Regions", destination: "regions" },
  { href: "/squadron", label: "Squadrons", destination: "squadrons" },
  { href: "/search", label: "Search", destination: "search" },
  { href: "/stories", label: "Stories", destination: "stories" },
  { href: "/insights", label: "Insights", destination: "insights" },
  { href: "/about", label: "About", destination: "about" },
];

const linkStyle: React.CSSProperties = {
  color: "#c9b98a",
  fontFamily: "'Helvetica Neue', Arial, sans-serif",
  fontSize: "0.875rem",
  textTransform: "uppercase",
  letterSpacing: "0.1em",
  textDecoration: "none",
  opacity: 0.85,
  minHeight: 44,
  display: "inline-flex",
  alignItems: "center",
};

export default function Header() {
  // Phones get a menu button; seven links don't fit across a 390px screen.
  const [open, setOpen] = useState(false);

  return (
    <header
      style={{
        backgroundColor: "#1a2332",
        borderBottom: "3px solid #8b7355",
      }}
    >
      <div
        className="flex-nowrap md:flex-wrap"
        style={{
          maxWidth: 1200,
          margin: "0 auto",
          padding: "1rem 1.5rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "1rem",
        }}
      >
        <Link
          href="/"
          style={{
            color: "#c9b98a",
            fontSize: "1.25rem",
            fontFamily: "'Helvetica Neue', Arial, sans-serif",
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: "0.15em",
            textDecoration: "none",
            display: "inline-flex",
            alignItems: "center",
            minHeight: 44,
          }}
        >
          Bomber Command Memorial Register
        </Link>
        <nav
          className="hidden md:flex"
          aria-label="Main"
          style={{
            gap: "1.5rem",
            alignItems: "center",
          }}
        >
          {NAV_LINKS.map((l) => (
            <Link key={l.href} href={l.href} onClick={() => trackNav(l.destination)} style={linkStyle}>
              {l.label}
            </Link>
          ))}
        </nav>
        <button
          type="button"
          className="md:hidden"
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
          aria-controls="mobile-nav"
          onClick={() => setOpen((o) => !o)}
          style={{
            background: "none",
            border: "1px solid #8b7355",
            borderRadius: 6,
            color: "#c9b98a",
            width: 44,
            height: 44,
            flexShrink: 0,
            fontSize: "1.4rem",
            lineHeight: 1,
            cursor: "pointer",
          }}
        >
          {open ? "✕" : "☰"}
        </button>
      </div>
      {open && (
        <nav
          id="mobile-nav"
          className="md:hidden"
          aria-label="Main"
          style={{
            display: "flex",
            flexDirection: "column",
            padding: "0 1.5rem 0.75rem",
            borderTop: "1px solid #2c3e50",
          }}
        >
          {NAV_LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              onClick={() => {
                trackNav(l.destination);
                setOpen(false);
              }}
              style={{ ...linkStyle, fontSize: "1rem", borderBottom: "1px solid #2c3e50", width: "100%" }}
            >
              {l.label}
            </Link>
          ))}
        </nav>
      )}
    </header>
  );
}
