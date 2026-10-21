"use client";

import Link from "next/link";

function trackNav(destination: string) {
  (window as { posthog?: { capture: (e: string, p?: Record<string, unknown>) => void } }).posthog?.capture("nav_click", { destination });
}

export default function Header() {
  return (
    <header
      style={{
        backgroundColor: "#1a2332",
        borderBottom: "3px solid #8b7355",
      }}
    >
      <div
        style={{
          maxWidth: 1200,
          margin: "0 auto",
          padding: "1rem 1.5rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
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
          }}
        >
          Bomber Command Memorial Register
        </Link>
        <nav
          style={{
            display: "flex",
            gap: "1.5rem",
            alignItems: "center",
          }}
        >
          <Link
            href="/"
            onClick={() => trackNav("home")}
            style={{
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
            }}
          >
            Home
          </Link>
          <Link
            href="/region/united-kingdom"
            onClick={() => trackNav("regions")}
            style={{
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
            }}
          >
            Regions
          </Link>
          <Link
            href="/squadron"
            onClick={() => trackNav("squadrons")}
            style={{
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
            }}
          >
            Squadrons
          </Link>
          <Link
            href="/search"
            onClick={() => trackNav("search")}
            style={{
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
            }}
          >
            Search
          </Link>
          <Link
            href="/stories"
            onClick={() => trackNav("stories")}
            style={{
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
            }}
          >
            Stories
          </Link>
          <Link
            href="/insights"
            onClick={() => trackNav("insights")}
            style={{
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
            }}
          >
            Insights
          </Link>
          <Link
            href="/about"
            onClick={() => trackNav("about")}
            style={{
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
            }}
          >
            About
          </Link>
        </nav>
      </div>
    </header>
  );
}
