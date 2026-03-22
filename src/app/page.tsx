import { getAllMemorials, getMemorialStats, getFeaturedMemorials } from "@/lib/data";
import MemorialCard from "@/components/MemorialCard";
import SearchBar from "@/components/SearchBar";
import MemorialMap from "@/components/MemorialMap";

export default function HomePage() {
  const memorials = getAllMemorials();
  const stats = getMemorialStats();
  const featured = getFeaturedMemorials();

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
        {/* Subtle gold accent line */}
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

        {/* Gold divider */}
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

      {/* Map Section */}
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
            marginBottom: "1rem",
            textAlign: "center",
          }}
        >
          Memorial Locations
        </h2>
        <p
          style={{
            textAlign: "center",
            color: "#666",
            marginBottom: "1.5rem",
            fontSize: "0.95rem",
          }}
        >
          Showing memorials with known coordinates. Many more locations are being
          researched.
        </p>
        <MemorialMap memorials={memorials} />
      </section>

      {/* Featured Memorials */}
      {featured.length > 0 && (
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
            {featured.map((memorial) => (
              <MemorialCard key={memorial.id} memorial={memorial} />
            ))}
          </div>
        </section>
      )}

      {/* Recent Additions */}
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
          All Memorials
        </h2>
        <p
          style={{
            textAlign: "center",
            color: "#666",
            marginBottom: "2rem",
            fontSize: "0.95rem",
          }}
        >
          Browse the complete register of {stats.totalMemorials} memorials.
        </p>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
            gap: "1.5rem",
          }}
        >
          {memorials.slice(0, 12).map((memorial) => (
            <MemorialCard key={memorial.id} memorial={memorial} />
          ))}
        </div>
        {memorials.length > 12 && (
          <p
            style={{
              textAlign: "center",
              marginTop: "2rem",
              color: "#8b7355",
              fontStyle: "italic",
            }}
          >
            Showing 12 of {memorials.length} memorials. Use the search above or
            browse by region.
          </p>
        )}
      </section>
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
