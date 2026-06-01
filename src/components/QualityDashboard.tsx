"use client";

import { useState, useMemo } from "react";
import Link from "next/link";

interface SectionScore {
  section: string;
  score: number;
  issues: string[];
}

interface MemorialQuality {
  slug: string;
  title: string;
  overallScore: number;
  dataQuality: string;
  sections: SectionScore[];
  capsRatio: number;
  bracketCount: number;
  slashCount: number;
  hasInscription: boolean;
  hasNarrative: boolean;
  hasCrew: boolean;
  hasCoordinates: boolean;
  hasPhotos: boolean;
  crewCount: number;
  crewWithRank: number;
  crewWithAge: number;
  crewWithNationality: number;
  lastUpdated: string;
}

const NAVY = "#1a2332";
const GOLD = "#c9b98a";

function ScoreBadge({ score }: { score: number }) {
  const bg = score >= 80 ? "#1a4a1a" : score >= 50 ? "#4a3800" : score >= 25 ? "#5a3a1e" : "#5a1a1a";
  const text = score >= 80 ? "#7ecb7e" : score >= 50 ? "#d4b84a" : score >= 25 ? "#d4a88c" : "#e88c8c";
  return (
    <span style={{
      display: "inline-block",
      padding: "2px 8px",
      borderRadius: 4,
      fontSize: "0.75rem",
      fontWeight: 700,
      backgroundColor: bg,
      color: text,
      fontFamily: "monospace",
      minWidth: 35,
      textAlign: "center",
    }}>
      {score}
    </span>
  );
}

export default function QualityDashboard({ data }: { data: MemorialQuality[] }) {
  const [sortBy, setSortBy] = useState<"score" | "title" | "crew" | "caps">("score");
  const [filterBottom5, setFilterBottom5] = useState(false);
  const [expandedSlug, setExpandedSlug] = useState<string | null>(null);

  const sorted = useMemo(() => {
    const items = [...data];
    switch (sortBy) {
      case "score": items.sort((a, b) => a.overallScore - b.overallScore); break;
      case "title": items.sort((a, b) => a.title.localeCompare(b.title)); break;
      case "crew": items.sort((a, b) => b.crewCount - a.crewCount); break;
      case "caps": items.sort((a, b) => b.capsRatio - a.capsRatio); break;
    }
    return items;
  }, [data, sortBy]);

  const threshold5 = useMemo(() => {
    const scores = data.map(d => d.overallScore).sort((a, b) => a - b);
    return scores[Math.floor(scores.length * 0.05)] || 0;
  }, [data]);

  const displayed = filterBottom5 ? sorted.filter(d => d.overallScore <= threshold5) : sorted;

  // Summary stats
  const avgScore = Math.round(data.reduce((s, d) => s + d.overallScore, 0) / data.length);
  const withNarrative = data.filter(d => d.hasNarrative).length;
  const withCrew = data.filter(d => d.hasCrew).length;
  const withCoords = data.filter(d => d.hasCoordinates).length;
  const withInscription = data.filter(d => d.hasInscription).length;
  const totalIssues = data.reduce((s, d) => s + d.sections.reduce((ss, sec) => ss + sec.issues.length, 0), 0);

  return (
    <div>
      {/* Summary cards */}
      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", marginBottom: "1.5rem" }}>
        {[
          { label: "Total Pages", value: data.length },
          { label: "Avg Score", value: avgScore },
          { label: "With Narrative", value: `${withNarrative} (${Math.round(withNarrative/data.length*100)}%)` },
          { label: "With Crew", value: `${withCrew} (${Math.round(withCrew/data.length*100)}%)` },
          { label: "With Coords", value: `${withCoords} (${Math.round(withCoords/data.length*100)}%)` },
          { label: "With Inscription", value: `${withInscription} (${Math.round(withInscription/data.length*100)}%)` },
          { label: "Total Issues", value: totalIssues },
          { label: "Bottom 5% Threshold", value: `<= ${threshold5}` },
        ].map(card => (
          <div key={card.label} style={{
            background: `linear-gradient(135deg, ${NAVY} 0%, #243447 100%)`,
            borderRadius: 8,
            padding: "0.75rem 1rem",
            flex: "1 1 140px",
            minWidth: 130,
          }}>
            <div style={{ fontSize: "1.25rem", fontWeight: 700, color: GOLD, fontFamily: "monospace" }}>{card.value}</div>
            <div style={{ fontSize: "0.7rem", color: "rgba(255,255,255,0.5)", textTransform: "uppercase", letterSpacing: "0.05em" }}>{card.label}</div>
          </div>
        ))}
      </div>

      {/* Score distribution */}
      <div style={{
        background: "#fff",
        border: "1px solid #e8e4de",
        borderRadius: 8,
        padding: "1rem",
        marginBottom: "1.5rem",
      }}>
        <h3 style={{ margin: "0 0 0.5rem", fontSize: "0.85rem", color: NAVY }}>Score Distribution</h3>
        <div style={{ display: "flex", gap: 2, alignItems: "flex-end", height: 60 }}>
          {[0, 10, 20, 30, 40, 50, 60, 70, 80, 90].map(bucket => {
            const count = data.filter(d => d.overallScore >= bucket && d.overallScore < bucket + 10).length;
            const maxCount = Math.max(...[0, 10, 20, 30, 40, 50, 60, 70, 80, 90].map(b =>
              data.filter(d => d.overallScore >= b && d.overallScore < b + 10).length));
            const height = maxCount > 0 ? (count / maxCount) * 50 + 2 : 2;
            const bg = bucket < 30 ? "#e88c8c" : bucket < 50 ? "#d4a88c" : bucket < 70 ? "#d4b84a" : "#7ecb7e";
            return (
              <div key={bucket} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 2 }}>
                <div style={{ fontSize: "0.6rem", color: "#888" }}>{count}</div>
                <div style={{ width: "100%", height, backgroundColor: bg, borderRadius: 2 }} />
                <div style={{ fontSize: "0.55rem", color: "#aaa" }}>{bucket}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Controls */}
      <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem", alignItems: "center", flexWrap: "wrap" }}>
        <label style={{ fontSize: "0.8rem", color: "#666" }}>
          Sort:
          <select value={sortBy} onChange={e => setSortBy(e.target.value as typeof sortBy)} style={{ marginLeft: 4, padding: "2px 6px", fontSize: "0.8rem" }}>
            <option value="score">Score (worst first)</option>
            <option value="title">Title (A-Z)</option>
            <option value="crew">Crew count</option>
            <option value="caps">Caps ratio</option>
          </select>
        </label>
        <label style={{ fontSize: "0.8rem", color: "#666", cursor: "pointer" }}>
          <input type="checkbox" checked={filterBottom5} onChange={e => setFilterBottom5(e.target.checked)} style={{ marginRight: 4 }} />
          Show bottom 5% only ({data.filter(d => d.overallScore <= threshold5).length} pages)
        </label>
        <span style={{ fontSize: "0.75rem", color: "#999" }}>
          Showing {displayed.length} of {data.length}
        </span>
      </div>

      {/* Table */}
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem" }}>
          <thead>
            <tr style={{ borderBottom: "2px solid #e8e4de", textAlign: "left" }}>
              <th style={{ padding: "0.5rem", color: NAVY }}>Memorial</th>
              <th style={{ padding: "0.5rem", color: NAVY, width: 50 }}>Score</th>
              <th style={{ padding: "0.5rem", color: NAVY, width: 60 }}>Quality</th>
              <th style={{ padding: "0.5rem", color: NAVY, width: 40 }}>Narr</th>
              <th style={{ padding: "0.5rem", color: NAVY, width: 40 }}>Insc</th>
              <th style={{ padding: "0.5rem", color: NAVY, width: 40 }}>Crew</th>
              <th style={{ padding: "0.5rem", color: NAVY, width: 40 }}>Coords</th>
              <th style={{ padding: "0.5rem", color: NAVY, width: 40 }}>Caps%</th>
              <th style={{ padding: "0.5rem", color: NAVY, width: 50 }}>Issues</th>
            </tr>
          </thead>
          <tbody>
            {displayed.map(m => {
              const issueCount = m.sections.reduce((s, sec) => s + sec.issues.length, 0);
              const isBottom5 = m.overallScore <= threshold5;
              return (
                <tr
                  key={m.slug}
                  style={{
                    borderBottom: "1px solid #f0ede8",
                    backgroundColor: isBottom5 ? "#fff5f5" : expandedSlug === m.slug ? "#f8f6f2" : "transparent",
                    cursor: "pointer",
                  }}
                  onClick={() => setExpandedSlug(expandedSlug === m.slug ? null : m.slug)}
                >
                  <td style={{ padding: "0.5rem" }}>
                    <Link href={`/memorial/${m.slug}`} style={{ color: "#7a4500", textDecoration: "none", fontSize: "0.8rem" }} onClick={e => e.stopPropagation()}>
                      {m.title.length > 50 ? m.title.slice(0, 47) + '...' : m.title}
                    </Link>
                  </td>
                  <td style={{ padding: "0.5rem" }}><ScoreBadge score={m.overallScore} /></td>
                  <td style={{ padding: "0.5rem", fontSize: "0.7rem", color: "#888" }}>{m.dataQuality}</td>
                  <td style={{ padding: "0.5rem", textAlign: "center" }}>{m.hasNarrative ? "Y" : "—"}</td>
                  <td style={{ padding: "0.5rem", textAlign: "center" }}>{m.hasInscription ? "Y" : "—"}</td>
                  <td style={{ padding: "0.5rem", textAlign: "center" }}>{m.crewCount || "—"}</td>
                  <td style={{ padding: "0.5rem", textAlign: "center" }}>{m.hasCoordinates ? "Y" : "—"}</td>
                  <td style={{ padding: "0.5rem", textAlign: "center", color: m.capsRatio > 50 ? "#c44" : "#888" }}>{m.capsRatio}</td>
                  <td style={{ padding: "0.5rem", textAlign: "center", color: issueCount > 0 ? "#c44" : "#888" }}>{issueCount}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Expanded detail */}
      {expandedSlug && (() => {
        const m = data.find(d => d.slug === expandedSlug);
        if (!m) return null;
        return (
          <div style={{
            marginTop: "0.5rem",
            padding: "1rem",
            background: "#f8f6f2",
            borderRadius: 8,
            border: "1px solid #e8e4de",
          }}>
            <h4 style={{ margin: "0 0 0.5rem", fontSize: "0.9rem", color: NAVY }}>{m.title}</h4>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: "0.5rem" }}>
              {m.sections.map(sec => (
                <div key={sec.section} style={{
                  background: "#fff",
                  borderRadius: 6,
                  padding: "0.5rem 0.75rem",
                  border: `1px solid ${sec.score < 50 ? '#e8c4c4' : '#e8e4de'}`,
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.25rem" }}>
                    <span style={{ fontSize: "0.75rem", fontWeight: 600, color: NAVY }}>{sec.section}</span>
                    <ScoreBadge score={sec.score} />
                  </div>
                  {sec.issues.length > 0 && (
                    <ul style={{ margin: 0, padding: "0 0 0 1rem", fontSize: "0.7rem", color: "#c44" }}>
                      {sec.issues.map((issue, i) => <li key={i}>{issue}</li>)}
                    </ul>
                  )}
                </div>
              ))}
            </div>
            <div style={{ marginTop: "0.5rem", fontSize: "0.7rem", color: "#999" }}>
              Crew: {m.crewCount} total, {m.crewWithRank} with rank, {m.crewWithAge} with age, {m.crewWithNationality} with nationality
              {m.lastUpdated && ` | Last updated: ${m.lastUpdated}`}
              | Brackets: {m.bracketCount} | Slashes: {m.slashCount}
            </div>
          </div>
        );
      })()}
    </div>
  );
}
