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
  // getCountryCodes() already includes stub regions (Canada, France, NZ, Belgium)
  // with count: 0 — so static pages are generated for them even with no active data.
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
        }}
      >
        <nav style={{ marginBottom: "1.5rem", fontSize: "0.85rem" }}>
          <Link href="/" style={{ color: "#2c5f8a" }}>Home</Link>
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
          Bomber Command Memorials in {regionName}
        </h1>
        <p style={{ color: "#666", marginBottom: "2rem" }}>
          0 crash-site memorials recorded · research in progress
        </p>
        <p style={{
          color: "#444",
          lineHeight: 1.75,
          marginBottom: "2rem",
          fontSize: "1rem",
        }}>
          Bomber Command memorials in {regionName} — we&apos;re researching memorials
          in this region. If you have information about Bomber Command crash sites
          or memorials in {regionName}, we&apos;d love to hear from you.
        </p>
        <div style={{
          backgroundColor: "#faf8f4",
          border: "1px solid #e0dcd5",
          borderLeft: "3px solid #c9b98a",
          borderRadius: "0 8px 8px 0",
          padding: "1.5rem 2rem",
          marginBottom: "2rem",
        }}>
          <p style={{ color: "#8b7355", fontStyle: "italic", lineHeight: 1.7, marginBottom: "0.75rem" }}>
            Do you know of a Bomber Command crash site or memorial in {regionName}? We welcome contributions from researchers, local communities, veterans&apos; families and aviation historians.
          </p>
          <a
            href={`mailto:admin@bombermemorial.co.uk?subject=Memorial%20suggestion%3A%20${encodeURIComponent(regionName)}&body=I%20would%20like%20to%20suggest%20a%20memorial%20in%20${encodeURIComponent(regionName)}%3A%0A%0A`}
            style={{
              display: "inline-block",
              padding: "0.45rem 1.25rem",
              backgroundColor: "#1a2332",
              color: "#c9b98a",
              borderRadius: 6,
              fontSize: "0.85rem",
              fontFamily: "'Helvetica Neue', Arial, sans-serif",
              textDecoration: "none",
              letterSpacing: "0.03em",
            }}
          >
            Contribute to this region
          </a>
        </div>
        <Link href="/" style={{ color: "#2c5f8a", fontSize: "0.9rem" }}>
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
    <div data-pagefind-ignore style={{ maxWidth: 1200, margin: "0 auto", padding: "2rem 1.5rem" }}>
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
