import Image from "next/image";
import { CrewMember } from "@/lib/types";

interface CrewTableProps {
  crew: CrewMember[];
}

export default function CrewTable({ crew }: CrewTableProps) {
  const hasBios = crew.some((m) => m.bio || m.hometown || m.fate_detail);

  return (
    <div>
      {/* Summary table */}
      <div style={{ overflowX: "auto" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontSize: "0.9rem",
            backgroundColor: "#ffffff",
            borderRadius: 8,
            overflow: "hidden",
            border: "1px solid #e0dcd5",
          }}
        >
          <thead>
            <tr
              style={{
                backgroundColor: "#1a2332",
                color: "#c9b98a",
              }}
            >
              <th style={thStyle}>Rank</th>
              <th style={thStyle}>Name</th>
              <th style={thStyle}>Role</th>
              <th style={thStyle}>Age</th>
              <th style={thStyle}>Nationality</th>
              <th style={thStyle}>Fate</th>
              <th style={{ ...thStyle, minWidth: 200 }}>Burial / Status</th>
            </tr>
          </thead>
          <tbody>
            {crew.map((member, index) => (
              <tr
                key={index}
                style={{
                  backgroundColor: index % 2 === 0 ? "#ffffff" : "#f9f7f4",
                  borderBottom: "1px solid #e0dcd5",
                }}
              >
                <td style={tdStyle}>{member.rank || "\u2014"}</td>
                <td style={{ ...tdStyle, fontWeight: 600 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    {member.photo && (
                      <div style={{
                        width: 48,
                        height: 48,
                        borderRadius: "50%",
                        overflow: "hidden",
                        flexShrink: 0,
                        border: "2px solid #e0dcd5",
                        position: "relative",
                      }}>
                        <Image
                          src={`/images/memorials/${member.photo}`}
                          alt={`${member.name} portrait`}
                          fill
                          style={{ objectFit: "cover" }}
                          unoptimized
                        />
                      </div>
                    )}
                    <div>
                      {member.name}
                      {member.service_number && member.service_number !== "\u2014" && (
                        <div style={{ fontSize: "0.75rem", color: "#999", fontWeight: 400 }}>
                          {member.service_number}
                        </div>
                      )}
                    </div>
                  </div>
                </td>
                <td style={tdStyle}>{member.role || "\u2014"}</td>
                <td style={tdStyle}>{member.age || "\u2014"}</td>
                <td style={tdStyle}>{member.nationality || "\u2014"}</td>
                <td style={tdStyle}>
                  <span
                    style={{
                      display: "inline-block",
                      padding: "0.15rem 0.5rem",
                      borderRadius: 8,
                      fontSize: "0.8rem",
                      fontWeight: 500,
                      backgroundColor:
                        member.fate === "Killed" || member.fate === "Killed in action"
                          ? "#f5e8e8"
                          : member.fate === "Survived" || member.fate === "Survived injured"
                          ? "#e8f5e8"
                          : member.fate === "POW" || member.fate === "Prisoner of War"
                          ? "#e8ecf5"
                          : member.fate === "MIA" || member.fate === "Missing"
                          ? "#f5f0e8"
                          : "#f5f5f5",
                      color:
                        member.fate === "Killed" || member.fate === "Killed in action"
                          ? "#8b3a3a"
                          : member.fate === "Survived" || member.fate === "Survived injured"
                          ? "#3a6b3a"
                          : member.fate === "POW" || member.fate === "Prisoner of War"
                          ? "#3a4a8b"
                          : member.fate === "MIA" || member.fate === "Missing"
                          ? "#8b6b3a"
                          : "#666",
                    }}
                  >
                    {member.fate || "\u2014"}
                  </span>
                  {member.decorations && (
                    <div style={{ fontSize: "0.75rem", color: "#8b7355", marginTop: "0.25rem" }}>
                      {member.decorations}
                    </div>
                  )}
                </td>
                <td style={{ ...tdStyle, fontSize: "0.8rem" }}>
                  {member.cwgc_url ? (
                    <a
                      href={member.cwgc_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: "#7a4500" }}
                    >
                      {member.burial_location && member.burial_location !== "\u2014"
                        ? member.burial_location
                        : "CWGC Record"}
                    </a>
                  ) : (
                    member.burial_location && member.burial_location !== "\u2014"
                      ? member.burial_location
                      : "\u2014"
                  )}
                  {member.cwgc_verified && (
                    <span
                      style={{
                        fontSize: "0.65rem",
                        marginLeft: "0.4rem",
                        padding: "0.1rem 0.4rem",
                        borderRadius: 6,
                        backgroundColor: "#e8f5e8",
                        color: "#3a6b3a",
                      }}
                    >
                      CWGC
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Individual crew bios */}
      {hasBios && (
        <div style={{ marginTop: "1.5rem" }}>
          <h3
            style={{
              fontFamily: "'Helvetica Neue', Arial, sans-serif",
              color: "#1a2332",
              fontSize: "1.1rem",
              marginBottom: "1rem",
            }}
          >
            About the Crew
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {crew
              .filter((m) => m.bio || m.hometown || m.fate_detail)
              .map((member, index) => (
                <div
                  key={index}
                  style={{
                    backgroundColor: "#ffffff",
                    border: "1px solid #e0dcd5",
                    borderLeft: "3px solid #8b7355",
                    borderRadius: "0 8px 8px 0",
                    padding: "1rem 1.25rem",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                      marginBottom: "0.5rem",
                      flexWrap: "wrap",
                    }}
                  >
                    <span style={{ fontWeight: 600, color: "#1a2332" }}>
                      {member.rank} {member.name}
                    </span>
                    {member.age && (
                      <span style={{ fontSize: "0.85rem", color: "#666" }}>
                        (age {member.age})
                      </span>
                    )}
                    <span style={{ fontSize: "0.85rem", color: "#8b7355" }}>
                      {member.role}
                    </span>
                    {member.decorations && (
                      <span
                        style={{
                          fontSize: "0.7rem",
                          padding: "0.1rem 0.5rem",
                          borderRadius: 8,
                          backgroundColor: "#f5f0e8",
                          color: "#8b6b3a",
                        }}
                      >
                        {member.decorations}
                      </span>
                    )}
                  </div>
                  {member.hometown && (
                    <p style={{ fontSize: "0.85rem", color: "#666", margin: "0 0 0.4rem" }}>
                      From {member.hometown}
                    </p>
                  )}
                  {member.fate_detail && (
                    <p style={{
                      fontSize: "0.9rem",
                      color: "#555",
                      lineHeight: 1.7,
                      margin: member.bio ? "0 0 0.4rem" : 0,
                      fontStyle: "italic",
                      borderLeft: "2px solid #c9b98a",
                      paddingLeft: "0.75rem",
                    }}>
                      {member.fate_detail}
                    </p>
                  )}
                  {member.bio && (
                    <p style={{ fontSize: "0.9rem", color: "#444", lineHeight: 1.7, margin: 0 }}>
                      {member.bio}
                    </p>
                  )}
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}

const thStyle: React.CSSProperties = {
  padding: "0.75rem 1rem",
  textAlign: "left",
  fontFamily: "'Helvetica Neue', Arial, sans-serif",
  fontSize: "0.75rem",
  textTransform: "uppercase",
  letterSpacing: "0.05em",
  fontWeight: 600,
};

const tdStyle: React.CSSProperties = {
  padding: "0.75rem 1rem",
  verticalAlign: "top",
};
