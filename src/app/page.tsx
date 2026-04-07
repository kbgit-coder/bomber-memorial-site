import { getAllMemorials, getMemorialStats, getCountryCodes, getMemorialBySlug } from "@/lib/data";
import SearchBar from "@/components/SearchBar";
import Link from "next/link";
import { Memorial } from "@/lib/types";

// Strip heavy fields to reduce page payload
function toLightMemorial(m: Memorial): Memorial {
  return {
    id: m.id,
    title: m.title,
    location_name: m.location_name,
    county: m.county,
    country: m.country,
    region_code: m.region_code,
    crash_date: m.crash_date,
    aircraft_type: m.aircraft_type,
    serial_number: m.serial_number,
    squadron: m.squadron,
    data_quality: m.data_quality,
    memorial_type: m.memorial_type,
  };
}

// Featured memorials keep narrative excerpt + external narrative count
function toFeaturedMemorial(m: Memorial) {
  return {
    id: m.id,
    title: m.title,
    location_name: m.location_name,
    county: m.county,
    country: m.country,
    crash_date: m.crash_date,
    aircraft_type: m.aircraft_type,
    serial_number: m.serial_number,
    squadron: m.squadron,
    data_quality: m.data_quality,
    narrative_excerpt: m.narrative ? m.narrative.slice(0, 200) + (m.narrative.length > 200 ? "..." : "") : undefined,
    crew_count: m.crew?.length || 0,
    external_narratives_count: m.external_narratives?.length || 0,
  };
}

export default function HomePage() {
  const allMemorials = getAllMemorials();
  const stats = getMemorialStats();
  const regions = getCountryCodes();

  // Light versions for search (no narratives, crew arrays, coords, or sources)
  const memorials = allMemorials.map(toLightMemorial);

  // Hand-picked flagship records — updated quarterly
  const flagshipSlugs = [
    "farnsfield-halifax-mz519",
    "elsham-wolds-jd386",
    "cloot-drove-nd981-and-lancaster-me625-mid-air-collision-",
    "kirkley-lowestoft-halifax-memorial-general-memorial-to-196",
    "higher-shelf-stones-overexposed-memorial-b-29-44-61999",
  ];
  const flagshipCards = flagshipSlugs
    .map(slug => getMemorialBySlug(slug))
    .filter(Boolean)
    .map(m => toFeaturedMemorial(m!));

  return (
    <div data-pagefind-ignore>
      {/* Hero Section */}
      <section
        style={{
          background: "linear-gradient(135deg, #1a2332 0%, #2c3e50 100%)",
          color: "#ffffff",
          padding: "5rem 1.5rem 4rem",
          textAlign: "center",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            position: "absolute",
            top: 0,
            left: "50%",
            transform: "translateX(-50%)",
            width: 60,
            height: 3,
            backgroundColor: "#c9b98a",
          }}
        />

        <h1
          style={{
            fontFamily: "'Helvetica Neue', Arial, sans-serif",
            fontSize: "clamp(1.75rem, 4vw, 2.75rem)",
            fontWeight: 600,
            color: "#ffffff",
            letterSpacing: "0.05em",
            marginBottom: "1rem",
            lineHeight: 1.2,
          }}
        >
          Bomber Command
          <br />
          <span style={{ color: "#c9b98a" }}>Memorial Register</span>
        </h1>

        <p
          style={{
            fontSize: "clamp(1rem, 2vw, 1.15rem)",
            color: "rgba(255,255,255,0.75)",
            maxWidth: 640,
            margin: "0 auto 1.5rem",
            lineHeight: 1.7,
          }}
        >
          A digital record of the memorials, crash sites, and aircrew of RAF
          Bomber Command during the Second World War. Lest we forget.
        </p>

        <div
          style={{
            width: 80,
            height: 1,
            backgroundColor: "#c9b98a",
            margin: "0 auto 2rem",
            opacity: 0.6,
          }}
        />

        {/* Stats */}
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: "3rem",
            flexWrap: "wrap",
          }}
        >
          <StatItem value={stats.totalMemorials} label="Memorials" />
          <StatItem value={stats.countries} label="Countries" />
          <StatItem value={stats.totalCrew} label="Crew Recorded" />
        </div>
      </section>

      {/* Search Section */}
      <section
        style={{
          maxWidth: 1200,
          margin: "-2rem auto 0",
          padding: "0 1.5rem",
          position: "relative",
          zIndex: 10,
        }}
      >
        <div
          style={{
            backgroundColor: "#ffffff",
            borderRadius: 12,
            padding: "1.5rem",
            boxShadow: "0 4px 20px rgba(0,0,0,0.08)",
            border: "1px solid #e0dcd5",
          }}
        >
          <SearchBar memorials={memorials} />
        </div>
      </section>

      {/* Browse by Region */}
      <section
        style={{
          maxWidth: 1200,
          margin: "3rem auto",
          padding: "0 1.5rem",
        }}
      >
        <h2
          style={{
            fontFamily: "'Helvetica Neue', Arial, sans-serif",
            color: "#1a2332",
            fontSize: "1.5rem",
            marginBottom: "0.5rem",
            textAlign: "center",
          }}
        >
          Browse by Region
        </h2>
        <p
          style={{
            textAlign: "center",
            color: "#666",
            marginBottom: "1.5rem",
            fontSize: "0.95rem",
          }}
        >
          Explore memorials across {stats.countries} countries.
        </p>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "center",
            gap: "0.75rem",
          }}
        >
          {regions.map((region) => (
            <Link
              key={region.code}
              href={`/region/${region.code}`}
              style={{
                display: "inline-block",
                padding: "0.5rem 1.25rem",
                backgroundColor: "#ffffff",
                border: "1px solid #e0dcd5",
                borderRadius: 20,
                fontFamily: "'Helvetica Neue', Arial, sans-serif",
                fontSize: "0.875rem",
                color: "#1a2332",
                textDecoration: "none",
                transition: "all 0.2s ease",
              }}
            >
              {region.name}{" "}
              <span style={{ color: "#8b7355", fontSize: "0.8rem" }}>
                ({region.count})
              </span>
            </Link>
          ))}
        </div>
      </section>

      {/* Featured Memorials */}
      {flagshipCards.length > 0 && (
        <section
          style={{
            maxWidth: 1200,
            margin: "3rem auto",
            padding: "0 1.5rem 2rem",
          }}
        >
          <h2
            style={{
              fontFamily: "'Helvetica Neue', Arial, sans-serif",
              color: "#1a2332",
              fontSize: "1.5rem",
              marginBottom: "0.5rem",
              textAlign: "center",
            }}
          >
            Featured Memorials
          </h2>
          <p
            style={{
              textAlign: "center",
              color: "#666",
              marginBottom: "2rem",
              fontSize: "0.95rem",
            }}
          >
            Some of the most detailed records in the register &mdash; showcasing crew stories, photographs, and community contributions.
          </p>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
              gap: "1.5rem",
            }}
          >
            {flagshipCards.map((card) => (
              <Link
                key={card.id}
                href={`/memorial/${card.id}`}
                style={{ textDecoration: "none" }}
              >
                <div
                  style={{
                    backgroundColor: "#ffffff",
                    border: "1px solid #e0dcd5",
                    borderRadius: 12,
                    padding: "1.5rem",
                    transition: "box-shadow 0.2s ease, transform 0.2s ease",
                    height: "100%",
                    display: "flex",
                    flexDirection: "column",
                  }}
                >
                  {/* Header row: title + quality badge */}
                  <div style={{ marginBottom: "0.75rem" }}>
                    <h3
                      style={{
                        fontFamily: "'Helvetica Neue', Arial, sans-serif",
                        color: "#1a2332",
                        fontSize: "1.1rem",
                        margin: "0 0 0.5rem",
                        lineHeight: 1.3,
                      }}
                    >
                      {card.title}
                    </h3>
                    <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                      <span
                        style={{
                          fontSize: "0.7rem",
                          padding: "0.15rem 0.6rem",
                          borderRadius: 10,
                          textTransform: "uppercase",
                          letterSpacing: "0.05em",
                          fontFamily: "'Helvetica Neue', Arial, sans-serif",
                          backgroundColor: card.data_quality === "Complete" ? "#2d5016" : "#5a4a1e",
                          color: card.data_quality === "Complete" ? "#a8d48c" : "#d4c98c",
                        }}
                      >
                        {card.data_quality}
                      </span>
                      {card.external_narratives_count > 0 && (
                        <span
                          style={{
                            fontSize: "0.7rem",
                            padding: "0.15rem 0.6rem",
                            borderRadius: 10,
                            fontFamily: "'Helvetica Neue', Arial, sans-serif",
                            backgroundColor: "#1a2332",
                            color: "#c9b98a",
                          }}
                        >
                          {card.external_narratives_count} external {card.external_narratives_count === 1 ? "source" : "sources"}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Location + date */}
                  <div style={{ fontSize: "0.85rem", color: "#666", marginBottom: "0.75rem" }}>
                    {card.location_name && <span>{card.location_name}</span>}
                    {card.county && <span>, {card.county}</span>}
                    {card.crash_date && (
                      <span style={{ marginLeft: "0.75rem", color: "#999" }}>
                        {card.crash_date}
                      </span>
                    )}
                  </div>

                  {/* Aircraft info */}
                  {(card.aircraft_type || card.squadron) && (
                    <div style={{ fontSize: "0.85rem", color: "#8b7355", marginBottom: "0.75rem" }}>
                      {card.aircraft_type}
                      {card.serial_number && ` ${card.serial_number}`}
                      {card.squadron && ` \u2022 ${card.squadron}`}
                    </div>
                  )}

                  {/* Narrative excerpt */}
                  {card.narrative_excerpt && (
                    <p
                      style={{
                        fontSize: "0.9rem",
                        color: "#555",
                        lineHeight: 1.6,
                        flex: 1,
                        marginBottom: "0.75rem",
                      }}
                    >
                      {card.narrative_excerpt}
                    </p>
                  )}

                  {/* Stats row */}
                  <div
                    style={{
                      display: "flex",
                      gap: "1.25rem",
                      fontSize: "0.8rem",
                      color: "#999",
                      borderTop: "1px solid #f0ece5",
                      paddingTop: "0.75rem",
                      marginTop: "auto",
                    }}
                  >
                    {card.crew_count > 0 && (
                      <span>{card.crew_count} crew recorded</span>
                    )}
                    <span style={{ marginLeft: "auto", color: "#2c5f8a" }}>
                      Read the full story &rarr;
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function StatItem({ value, label }: { value: number; label: string }) {
  return (
    <div style={{ textAlign: "center" }}>
      <div
        style={{
          fontSize: "2.25rem",
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
          fontWeight: 700,
          color: "#c9b98a",
          lineHeight: 1,
        }}
      >
        {value.toLocaleString()}
      </div>
      <div
        style={{
          fontSize: "0.8rem",
          color: "rgba(255,255,255,0.6)",
          textTransform: "uppercase",
          letterSpacing: "0.1em",
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
          marginTop: "0.25rem",
        }}
      >
        {label}
      </div>
    </div>
  );
}
