import { getAllMemorials, getMemorialStats, getFeaturedMemorials, getCountryCodes } from "@/lib/data";
import MemorialCard from "@/components/MemorialCard";
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

export default function HomePage() {
  const allMemorials = getAllMemorials();
  const stats = getMemorialStats();
  const featured = getFeaturedMemorials();
  const regions = getCountryCodes();

  // Light versions for search (no narratives, crew arrays, coords, or sources)
  const memorials = allMemorials.map(toLightMemorial);
  const featuredLight = featured.map(toLightMemorial);

  return (
    <div>
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
      {featuredLight.length > 0 && (
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
            Fully documented entries with crew details, narratives, and sources.
          </p>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
              gap: "1.5rem",
            }}
          >
            {featuredLight.map((memorial) => (
              <MemorialCard key={memorial.id} memorial={memorial} />
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
