import { Metadata } from "next";
import {
  getAllMemorialSlugs,
  getMemorialBySlug,
} from "@/lib/data";
import CrewTable from "@/components/CrewTable";
import StubCTA from "@/components/StubCTA";
import Link from "next/link";
import Image from "next/image";

interface Props {
  params: { slug: string };
}

export async function generateStaticParams() {
  const slugs = getAllMemorialSlugs();
  return slugs.map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const memorial = getMemorialBySlug(params.slug);
  if (!memorial) return { title: "Memorial Not Found" };

  return {
    title: memorial.title,
    description: memorial.narrative
      ? memorial.narrative.slice(0, 155) + "..."
      : `${memorial.title} - Bomber Command Memorial Register`,
  };
}

export default function MemorialPage({ params }: Props) {
  const memorial = getMemorialBySlug(params.slug);

  if (!memorial) {
    return (
      <div style={{ maxWidth: 800, margin: "4rem auto", padding: "0 1.5rem", textAlign: "center" }}>
        <h1 style={{ fontFamily: "'Helvetica Neue', Arial, sans-serif", color: "#1a2332" }}>
          Memorial Not Found
        </h1>
        <p>The memorial you are looking for could not be found.</p>
        <Link href="/" style={{ color: "#2c5f8a" }}>Return to the Register</Link>
      </div>
    );
  }

  const isFarnsfield = memorial.id === "farnsfield-halifax-mz519";

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "2rem 1.5rem" }}>
      {/* Breadcrumb */}
      <nav style={{ marginBottom: "1.5rem", fontSize: "0.85rem" }}>
        <Link href="/" style={{ color: "#2c5f8a" }}>Home</Link>
        <span style={{ color: "#999", margin: "0 0.5rem" }}>/</span>
        {memorial.country && (
          <>
            <Link
              href={`/region/${memorial.country.toLowerCase().replace(/\s+/g, "-")}`}
              style={{ color: "#2c5f8a" }}
            >
              {memorial.country}
            </Link>
            <span style={{ color: "#999", margin: "0 0.5rem" }}>/</span>
          </>
        )}
        <span style={{ color: "#999" }}>{memorial.title}</span>
      </nav>

      {/* Title */}
      <h1
        style={{
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
          color: "#1a2332",
          fontSize: "2rem",
          marginBottom: "0.5rem",
          lineHeight: 1.2,
        }}
      >
        {memorial.title}
      </h1>

      {memorial.location_name && (
        <p style={{ fontSize: "1.1rem", color: "#666", marginBottom: "0.5rem" }}>
          {memorial.location_name}
        </p>
      )}

      {/* Quality badge */}
      <div style={{ marginBottom: "2rem" }}>
        <span
          style={{
            fontSize: "0.75rem",
            padding: "0.25rem 0.75rem",
            borderRadius: 12,
            fontFamily: "'Helvetica Neue', Arial, sans-serif",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            backgroundColor:
              memorial.data_quality === "Complete"
                ? "#2d5016"
                : memorial.data_quality === "Partial"
                ? "#5a4a1e"
                : "#5a3a1e",
            color:
              memorial.data_quality === "Complete"
                ? "#a8d48c"
                : memorial.data_quality === "Partial"
                ? "#d4c98c"
                : "#d4a88c",
          }}
        >
          {memorial.data_quality || "Stub"} Record
        </span>
      </div>

      {/* Photos (Farnsfield) */}
      {isFarnsfield && (
        <section style={{ marginBottom: "2.5rem" }}>
          <h2 style={sectionHeading}>Photographs</h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
              gap: "1rem",
            }}
          >
            {[0, 1, 2, 3, 4, 5, 6].map((i) => (
              <div
                key={i}
                style={{
                  borderRadius: 8,
                  overflow: "hidden",
                  border: "1px solid #e0dcd5",
                  position: "relative",
                  aspectRatio: "4/3",
                }}
              >
                <Image
                  src={`/photos/image${i}.jpeg`}
                  alt={`${memorial.title} - photograph ${i + 1}`}
                  fill
                  style={{ objectFit: "cover" }}
                  sizes="(max-width: 600px) 100vw, 200px"
                />
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Narrative */}
      {memorial.narrative && (
        <section style={{ marginBottom: "2.5rem" }}>
          <h2 style={sectionHeading}>Narrative</h2>
          <div
            style={{
              backgroundColor: "#ffffff",
              border: "1px solid #e0dcd5",
              borderLeft: "3px solid #8b7355",
              borderRadius: "0 8px 8px 0",
              padding: "1.5rem 2rem",
              lineHeight: 1.8,
              fontSize: "1rem",
            }}
          >
            {memorial.narrative}
          </div>
        </section>
      )}

      {/* Aircraft Details */}
      {(memorial.aircraft_type ||
        memorial.serial_number ||
        memorial.squadron ||
        memorial.station) && (
        <section style={{ marginBottom: "2.5rem" }}>
          <h2 style={sectionHeading}>Aircraft &amp; Operation Details</h2>
          <div
            style={{
              backgroundColor: "#ffffff",
              border: "1px solid #e0dcd5",
              borderRadius: 8,
              padding: "1.5rem",
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
              gap: "1rem",
            }}
          >
            {memorial.aircraft_type && (
              <DetailItem label="Aircraft Type" value={memorial.aircraft_type} />
            )}
            {memorial.serial_number && (
              <DetailItem label="Serial Number" value={memorial.serial_number} />
            )}
            {memorial.aircraft_code && (
              <DetailItem label="Aircraft Code" value={memorial.aircraft_code} />
            )}
            {memorial.squadron && (
              <DetailItem label="Squadron" value={memorial.squadron} />
            )}
            {memorial.station && (
              <DetailItem label="Station" value={memorial.station} />
            )}
            {memorial.crash_date && (
              <DetailItem label="Date of Loss" value={memorial.crash_date} />
            )}
            {memorial.operation_type && (
              <DetailItem label="Operation Type" value={memorial.operation_type} />
            )}
            {memorial.operation_target && (
              <DetailItem label="Target" value={memorial.operation_target} />
            )}
            {memorial.cause_of_loss && (
              <DetailItem label="Cause of Loss" value={memorial.cause_of_loss} />
            )}
          </div>
        </section>
      )}

      {/* Crew */}
      {memorial.crew && memorial.crew.length > 0 && (
        <section style={{ marginBottom: "2.5rem" }}>
          <h2 style={sectionHeading}>
            Crew ({memorial.crew.length} {memorial.crew.length === 1 ? "member" : "members"})
          </h2>
          <CrewTable crew={memorial.crew} />
        </section>
      )}

      {memorial.crew_summary && !memorial.crew && (
        <section style={{ marginBottom: "2.5rem" }}>
          <h2 style={sectionHeading}>Crew</h2>
          <div
            style={{
              backgroundColor: "#ffffff",
              border: "1px solid #e0dcd5",
              borderRadius: 8,
              padding: "1.5rem",
            }}
          >
            {memorial.crew_summary}
          </div>
        </section>
      )}

      {/* Memorial Details */}
      {(memorial.memorial_type ||
        memorial.erected_by ||
        memorial.dedication_date ||
        memorial.condition) && (
        <section style={{ marginBottom: "2.5rem" }}>
          <h2 style={sectionHeading}>Memorial Details</h2>
          <div
            style={{
              backgroundColor: "#ffffff",
              border: "1px solid #e0dcd5",
              borderRadius: 8,
              padding: "1.5rem",
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
              gap: "1rem",
            }}
          >
            {memorial.memorial_type && (
              <DetailItem label="Type" value={memorial.memorial_type} />
            )}
            {memorial.erected_by && (
              <DetailItem label="Erected By" value={memorial.erected_by} />
            )}
            {memorial.dedication_date && (
              <DetailItem label="Dedication Date" value={memorial.dedication_date} />
            )}
            {memorial.condition && (
              <DetailItem label="Condition" value={memorial.condition} />
            )}
          </div>
        </section>
      )}

      {/* Sources */}
      {memorial.sources && memorial.sources.length > 0 && (
        <section style={{ marginBottom: "2.5rem" }}>
          <h2 style={sectionHeading}>Sources</h2>
          <ul
            style={{
              backgroundColor: "#ffffff",
              border: "1px solid #e0dcd5",
              borderRadius: 8,
              padding: "1.5rem 1.5rem 1.5rem 2.5rem",
              listStyle: "disc",
            }}
          >
            {memorial.sources.map((source, i) => (
              <li key={i} style={{ marginBottom: "0.5rem" }}>
                {source.url ? (
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ color: "#2c5f8a" }}
                  >
                    {source.title}
                  </a>
                ) : (
                  source.title
                )}
                {source.type && (
                  <span
                    style={{
                      fontSize: "0.75rem",
                      color: "#999",
                      marginLeft: "0.5rem",
                      fontStyle: "italic",
                    }}
                  >
                    ({source.type})
                  </span>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Contributor */}
      {memorial.contributor && (
        <p
          style={{
            fontSize: "0.85rem",
            color: "#999",
            fontStyle: "italic",
            textAlign: "right",
          }}
        >
          Record contributed by {memorial.contributor}
          {memorial.last_updated && ` \u2022 Last updated ${memorial.last_updated}`}
        </p>
      )}

      {/* Stub CTA */}
      <StubCTA
        quality={memorial.data_quality || "Stub"}
        title={memorial.title}
      />
    </div>
  );
}

function DetailItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div
        style={{
          fontSize: "0.7rem",
          color: "#999",
          textTransform: "uppercase",
          letterSpacing: "0.05em",
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
          marginBottom: "0.2rem",
        }}
      >
        {label}
      </div>
      <div style={{ fontWeight: 500, color: "#333" }}>{value}</div>
    </div>
  );
}

const sectionHeading: React.CSSProperties = {
  fontFamily: "'Helvetica Neue', Arial, sans-serif",
  color: "#1a2332",
  fontSize: "1.25rem",
  marginBottom: "1rem",
  paddingBottom: "0.5rem",
  borderBottom: "2px solid #e0dcd5",
};
