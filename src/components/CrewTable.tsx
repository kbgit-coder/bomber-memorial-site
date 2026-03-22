import { CrewMember } from "@/lib/types";

interface CrewTableProps {
  crew: CrewMember[];
}

export default function CrewTable({ crew }: CrewTableProps) {
  return (
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
            <th style={{ ...thStyle, minWidth: 200 }}>Burial Location</th>
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
                {member.name}
                {member.service_number && (
                  <div
                    style={{
                      fontSize: "0.75rem",
                      color: "#999",
                      fontWeight: 400,
                    }}
                  >
                    {member.service_number}
                  </div>
                )}
              </td>
              <td style={tdStyle}>{member.role || "\u2014"}</td>
              <td style={tdStyle}>{member.age || "\u2014"}</td>
              <td style={tdStyle}>{member.nationality || "\u2014"}</td>
              <td style={tdStyle}>
                <span
                  style={{
                    color:
                      member.fate === "Killed"
                        ? "#8b3a3a"
                        : member.fate === "Survived"
                        ? "#3a6b3a"
                        : "#666",
                    fontWeight: 500,
                  }}
                >
                  {member.fate || "\u2014"}
                </span>
              </td>
              <td style={{ ...tdStyle, fontSize: "0.8rem" }}>
                {member.burial_location || "\u2014"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
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
