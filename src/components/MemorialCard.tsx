import Link from "next/link";
import { Memorial } from "@/lib/types";

interface MemorialCardProps {
  memorial: Memorial;
}

export default function MemorialCard({ memorial }: MemorialCardProps) {
  const qualityBadge = {
    Complete: { bg: "#2d5016", text: "#a8d48c" },
    Partial: { bg: "#5a4a1e", text: "#d4c98c" },
    Stub: { bg: "#5a3a1e", text: "#d4a88c" },
  };

  const badge = qualityBadge[memorial.data_quality || "Stub"];

  return (
    <Link
      href={`/memorial/${memorial.id}`}
      style={{ textDecoration: "none", color: "inherit" }}
    >
      <article
        style={{
          backgroundColor: "#ffffff",
          border: "1px solid #e0dcd5",
          borderRadius: 8,
          padding: "1.5rem",
          transition: "box-shadow 0.2s ease, border-color 0.2s ease",
          cursor: "pointer",
          height: "100%",
          display: "flex",
          flexDirection: "column",
        }}
        className="memorial-card"
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: "0.75rem",
            gap: "0.5rem",
          }}
        >
          <h3
            style={{
              fontFamily: "'Helvetica Neue', Arial, sans-serif",
              color: "#1a2332",
              fontSize: "1.05rem",
              fontWeight: 600,
              margin: 0,
              lineHeight: 1.3,
            }}
          >
            {memorial.title}
          </h3>
          <span
            style={{
              backgroundColor: badge.bg,
              color: badge.text,
              fontSize: "0.65rem",
              padding: "0.15rem 0.5rem",
              borderRadius: 12,
              fontFamily: "'Helvetica Neue', Arial, sans-serif",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              whiteSpace: "nowrap",
              flexShrink: 0,
            }}
          >
            {memorial.data_quality || "Stub"}
          </span>
        </div>

        {memorial.location_name && (
          <p
            style={{
              fontSize: "0.875rem",
              color: "#666",
              margin: "0 0 0.5rem 0",
            }}
          >
            {memorial.location_name}
          </p>
        )}

        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "0.5rem",
            marginTop: "auto",
          }}
        >
          {memorial.aircraft_type && (
            <span
              style={{
                fontSize: "0.75rem",
                color: "#8b7355",
                backgroundColor: "#f5f3f0",
                padding: "0.2rem 0.5rem",
                borderRadius: 4,
                fontFamily: "'Helvetica Neue', Arial, sans-serif",
              }}
            >
              {memorial.aircraft_type}
            </span>
          )}
          {memorial.crash_date && (
            <span
              style={{
                fontSize: "0.75rem",
                color: "#8b7355",
                backgroundColor: "#f5f3f0",
                padding: "0.2rem 0.5rem",
                borderRadius: 4,
                fontFamily: "'Helvetica Neue', Arial, sans-serif",
              }}
            >
              {memorial.crash_date}
            </span>
          )}
          {memorial.squadron && (
            <span
              style={{
                fontSize: "0.75rem",
                color: "#8b7355",
                backgroundColor: "#f5f3f0",
                padding: "0.2rem 0.5rem",
                borderRadius: 4,
                fontFamily: "'Helvetica Neue', Arial, sans-serif",
              }}
            >
              {memorial.squadron}
            </span>
          )}
        </div>
      </article>
    </Link>
  );
}
