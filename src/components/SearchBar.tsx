"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { Memorial } from "@/lib/types";

interface SearchBarProps {
  memorials: Memorial[];
}

export default function SearchBar({ memorials }: SearchBarProps) {
  const [query, setQuery] = useState("");

  const results = useMemo(() => {
    if (query.length < 2) return [];
    const q = query.toLowerCase();
    return memorials
      .filter((m) => {
        const searchText = [
          m.title,
          m.location_name,
          m.aircraft_type,
          m.squadron,
          m.county,
          m.country,
          m.serial_number,
          m.crew?.map((c) => c.name).join(" "),
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();
        return searchText.includes(q);
      })
      .slice(0, 8);
  }, [query, memorials]);

  return (
    <div style={{ position: "relative", maxWidth: 600, margin: "0 auto" }}>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search memorials by name, location, aircraft, squadron, or crew..."
        style={{
          width: "100%",
          padding: "0.875rem 1.25rem",
          fontSize: "1rem",
          fontFamily: "Georgia, 'Times New Roman', serif",
          border: "2px solid #e0dcd5",
          borderRadius: 8,
          backgroundColor: "#ffffff",
          color: "#333",
          outline: "none",
          transition: "border-color 0.2s ease",
        }}
        onFocus={(e) => (e.target.style.borderColor = "#8b7355")}
        onBlur={(e) => (e.target.style.borderColor = "#e0dcd5")}
      />
      {results.length > 0 && (
        <div
          style={{
            position: "absolute",
            top: "100%",
            left: 0,
            right: 0,
            backgroundColor: "#ffffff",
            border: "1px solid #e0dcd5",
            borderTop: "none",
            borderRadius: "0 0 8px 8px",
            boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
            zIndex: 50,
            maxHeight: 400,
            overflowY: "auto",
          }}
        >
          {results.map((memorial) => (
            <Link
              key={memorial.id}
              href={`/memorial/${memorial.id}`}
              style={{
                display: "block",
                padding: "0.75rem 1.25rem",
                textDecoration: "none",
                color: "#333",
                borderBottom: "1px solid #f0ece6",
                transition: "background-color 0.15s ease",
              }}
              onClick={() => setQuery("")}
            >
              <div
                style={{
                  fontFamily: "'Helvetica Neue', Arial, sans-serif",
                  fontWeight: 600,
                  fontSize: "0.9rem",
                  color: "#1a2332",
                }}
              >
                {memorial.title}
              </div>
              <div style={{ fontSize: "0.8rem", color: "#888", marginTop: 2 }}>
                {[memorial.location_name, memorial.aircraft_type]
                  .filter(Boolean)
                  .join(" \u2022 ")}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
