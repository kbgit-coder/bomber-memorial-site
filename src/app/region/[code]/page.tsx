import { Metadata } from "next";
import {
  getCountryCodes,
  getMemorialsByRegionCode,
  getRegionName,
} from "@/lib/data";
import MemorialCard from "@/components/MemorialCard";
import Link from "next/link";

interface Props {
  params: { code: string };
}

export async function generateStaticParams() {
  const codes = getCountryCodes();
  return codes.map((c) => ({ code: c.code }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const name = getRegionName(params.code);
  return {
    title: `${name} Memorials`,
    description: `Bomber Command memorials in ${name}`,
  };
}

export default function RegionPage({ params }: Props) {
  const memorials = getMemorialsByRegionCode(params.code);
  const regionName = getRegionName(params.code);
  const allRegions = getCountryCodes();

  if (memorials.length === 0) {
    return (
      <div
        style={{
          maxWidth: 800,
          margin: "4rem auto",
          padding: "0 1.5rem",
          textAlign: "center",
        }}
      >
        <h1
          style={{
            fontFamily: "'Helvetica Neue', Arial, sans-serif",
            color: "#1a2332",
          }}
        >
          Region Not Found
        </h1>
        <Link href="/" style={{ color: "#2c5f8a" }}>
          Return to the Register
        </Link>
      </div>
    );
  }

  // Group by county for UK
  const byCounty: Record<string, typeof memorials> = {};
  if (regionName === "United Kingdom") {
    for (const m of memorials) {
      const county = m.county || "Other";
      if (!byCounty[county]) byCounty[county] = [];
      byCounty[county].push(m);
    }
  }

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: "2rem 1.5rem" }}>
      {/* Breadcrumb */}
      <nav style={{ marginBottom: "1.5rem", fontSize: "0.85rem" }}>
        <Link href="/" style={{ color: "#2c5f8a" }}>
          Home
        </Link>
        <span style={{ color: "#999", margin: "0 0.5rem" }}>/</span>
        <span style={{ color: "#999" }}>{regionName}</span>
      </nav>

      <h1
        style={{
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
          color: "#1a2332",
          fontSize: "2rem",
          marginBottom: "0.5rem",
        }}
      >
        {regionName}
      </h1>
      <p style={{ color: "#666", marginBottom: "2rem" }}>
        {memorials.length} memorial{memorials.length !== 1 ? "s" : ""} recorded
        in {regionName}.
      </p>

      {/* Region navigation */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "0.5rem",
          marginBottom: "2.5rem",
        }}
      >
        {allRegions.map((region) => (
          <Link
            key={region.code}
            href={`/region/${region.code}`}
            style={{
              padding: "0.4rem 0.85rem",
              borderRadius: 20,
              fontSize: "0.8rem",
              fontFamily: "'Helvetica Neue', Arial, sans-serif",
              textDecoration: "none",
              backgroundColor:
                region.code === params.code ? "#1a2332" : "#ffffff",
              color:
                region.code === params.code ? "#c9b98a" : "#1a2332",
              border: "1px solid #e0dcd5",
            }}
          >
            {region.name} ({region.count})
          </Link>
        ))}
      </div>

      {/* Memorials grouped by county (UK) or flat list */}
      {Object.keys(byCounty).length > 0 ? (
        Object.entries(byCounty)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([county, countyMemorials]) => (
            <div key={county} style={{ marginBottom: "2.5rem" }}>
              <h2
                style={{
                  fontFamily: "'Helvetica Neue', Arial, sans-serif",
                  color: "#1a2332",
                  fontSize: "1.25rem",
                  marginBottom: "1rem",
                  paddingBottom: "0.5rem",
                  borderBottom: "2px solid #e0dcd5",
                }}
              >
                {county}{" "}
                <span style={{ color: "#999", fontSize: "0.9rem", fontWeight: 400 }}>
                  ({countyMemorials.length})
                </span>
              </h2>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns:
                    "repeat(auto-fill, minmax(320px, 1fr))",
                  gap: "1.5rem",
                }}
              >
                {countyMemorials.map((m) => (
                  <MemorialCard key={m.id} memorial={m} />
                ))}
              </div>
            </div>
          ))
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
            gap: "1.5rem",
          }}
        >
          {memorials.map((m) => (
            <MemorialCard key={m.id} memorial={m} />
          ))}
        </div>
      )}
    </div>
  );
}
