import Link from "next/link";
import { getMemorialStats } from "@/lib/data";

export default function NotFound() {
  const stats = getMemorialStats();

  return (
    <div style={{
      maxWidth: 680,
      margin: "5rem auto",
      padding: "0 1.5rem",
      textAlign: "center",
    }}>
      {/* Heritage rule */}
      <div style={{
        width: 60,
        height: 3,
        backgroundColor: "#8b7355",
        margin: "0 auto 2rem",
      }} />

      {/* 404 indicator */}
      <div style={{
        fontFamily: "'Helvetica Neue', Arial, sans-serif",
        fontSize: "5rem",
        fontWeight: 700,
        color: "#1a2332",
        opacity: 0.12,
        lineHeight: 1,
        marginBottom: "-1rem",
        letterSpacing: "-0.04em",
      }}>
        404
      </div>

      {/* Primary heading */}
      <h1 style={{
        fontFamily: "'Helvetica Neue', Arial, sans-serif",
        color: "#1a2332",
        fontSize: "1.75rem",
        fontWeight: 600,
        lineHeight: 1.3,
        marginBottom: "1.25rem",
      }}>
        This memorial has not been found in our records
      </h1>

      {/* Respectful message */}
      <p style={{
        fontSize: "1.05rem",
        color: "#555",
        lineHeight: 1.8,
        marginBottom: "1rem",
      }}>
        The page you are looking for may have been moved, renamed, or may not yet exist
        in the register. Our records currently document{" "}
        <strong style={{ color: "#1a2332" }}>{stats.totalMemorials} memorials</strong>{" "}
        and the sacrifice of{" "}
        <strong style={{ color: "#1a2332" }}>{stats.totalCrew.toLocaleString()} aircrew</strong>{" "}
        across{" "}
        <strong style={{ color: "#1a2332" }}>{stats.countries} countries</strong>.
      </p>

      <p style={{
        fontSize: "0.95rem",
        color: "#777",
        lineHeight: 1.7,
        marginBottom: "2.5rem",
        fontStyle: "italic",
      }}>
        If you believe a memorial is missing from our register, we would welcome
        your contribution.
      </p>

      {/* Search prompt */}
      <div style={{
        backgroundColor: "#ffffff",
        border: "1px solid #e0dcd5",
        borderLeft: "3px solid #8b7355",
        borderRadius: "0 8px 8px 0",
        padding: "1.5rem 2rem",
        marginBottom: "2rem",
        textAlign: "left",
      }}>
        <p style={{
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
          color: "#1a2332",
          fontWeight: 600,
          fontSize: "0.95rem",
          marginBottom: "0.75rem",
        }}>
          Search the register
        </p>
        <p style={{ fontSize: "0.9rem", color: "#666", marginBottom: "1rem", lineHeight: 1.6 }}>
          Use our full-text search to find memorials by aircraft type, squadron, location,
          crew name, or crash date.
        </p>
        <Link href="/search" style={{
          display: "inline-block",
          padding: "0.6rem 1.5rem",
          backgroundColor: "#1a2332",
          color: "#c9b98a",
          borderRadius: 6,
          fontSize: "0.9rem",
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
          textDecoration: "none",
          letterSpacing: "0.03em",
        }}>
          Search the Memorial Register
        </Link>
      </div>

      {/* Navigation links */}
      <div style={{ display: "flex", gap: "1.5rem", justifyContent: "center", flexWrap: "wrap" }}>
        <Link href="/" style={{
          color: "#2c5f8a",
          fontSize: "0.9rem",
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
          textDecoration: "none",
        }}>
          Return to Home
        </Link>
        <span style={{ color: "#ccc" }}>|</span>
        <Link href="/region/united-kingdom" style={{
          color: "#2c5f8a",
          fontSize: "0.9rem",
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
          textDecoration: "none",
        }}>
          Browse UK Memorials
        </Link>
        <span style={{ color: "#ccc" }}>|</span>
        <Link href="/about" style={{
          color: "#2c5f8a",
          fontSize: "0.9rem",
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
          textDecoration: "none",
        }}>
          About the Register
        </Link>
      </div>

      {/* Bottom heritage rule */}
      <div style={{
        width: 60,
        height: 3,
        backgroundColor: "#8b7355",
        margin: "3rem auto 0",
      }} />
    </div>
  );
}
