import Link from "next/link";

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
            style={{
              color: "#c9b98a",
              fontFamily: "'Helvetica Neue', Arial, sans-serif",
              fontSize: "0.875rem",
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              textDecoration: "none",
              opacity: 0.85,
            }}
          >
            Home
          </Link>
          <Link
            href="/region/united-kingdom"
            style={{
              color: "#c9b98a",
              fontFamily: "'Helvetica Neue', Arial, sans-serif",
              fontSize: "0.875rem",
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              textDecoration: "none",
              opacity: 0.85,
            }}
          >
            Regions
          </Link>
          <Link
            href="/search"
            style={{
              color: "#c9b98a",
              fontFamily: "'Helvetica Neue', Arial, sans-serif",
              fontSize: "0.875rem",
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              textDecoration: "none",
              opacity: 0.85,
            }}
          >
            Search
          </Link>
          <Link
            href="/about"
            style={{
              color: "#c9b98a",
              fontFamily: "'Helvetica Neue', Arial, sans-serif",
              fontSize: "0.875rem",
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              textDecoration: "none",
              opacity: 0.85,
            }}
          >
            About
          </Link>
        </nav>
      </div>
    </header>
  );
}
