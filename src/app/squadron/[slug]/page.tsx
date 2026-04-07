import { Metadata } from "next";
import { getSquadronBySlug, getSquadronSlugs } from "@/lib/squadrons";
import MemorialMap from "@/components/MemorialMap";
import Link from "next/link";

interface Props {
  params: { slug: string };
}

export async function generateStaticParams() {
  return getSquadronSlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const squadron = getSquadronBySlug(params.slug);
  if (!squadron) return { title: "Squadron Not Found" };
  return {
    title: `${squadron.name} | Bomber Command Memorial Register`,
    description: `${squadron.memorials.length} memorials linked to ${squadron.name}. ${squadron.motto ? `Motto: "${squadron.motto}".` : ""} Bomber Command Memorial Register.`,
  };
}

export default function SquadronPage({ params }: Props) {
  const squadron = getSquadronBySlug(params.slug);

  if (!squadron) {
    return (
      <div style={{ maxWidth: 800, margin: "4rem auto", padding: "0 1.5rem", textAlign: "center" }}>
        <h1 style={{ fontFamily: "'Helvetica Neue', Arial, sans-serif", color: "#1a2332" }}>
          Squadron Not Found
        </h1>
        <Link href="/squadron" style={{ color: "#2c5f8a" }}>View all squadrons</Link>
      </div>
    );
  }

  const sectionStyle = {
    fontFamily: "'Helvetica Neue', Arial, sans-serif" as const,
    color: "#1a2332" as const,
    fontSize: "1.25rem" as const,
    marginBottom: "1rem" as const,
    paddingBottom: "0.5rem" as const,
    borderBottom: "2px solid #e0dcd5" as const,
  };

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "2rem 1.5rem" }}>
      {/* Breadcrumb */}
      <nav style={{ marginBottom: "1.5rem", fontSize: "0.85rem" }}>
        <Link href="/" style={{ color: "#2c5f8a" }}>Home</Link>
        <span style={{ color: "#999", margin: "0 0.5rem" }}>/</span>
        <Link href="/squadron" style={{ color: "#2c5f8a" }}>Squadrons</Link>
        <span style={{ color: "#999", margin: "0 0.5rem" }}>/</span>
        <span style={{ color: "#999" }}>{squadron.name}</span>
      </nav>

      {/* Header with badge */}
      <div style={{ display: "flex", alignItems: "flex-start", gap: "1.5rem", marginBottom: "2rem" }}>
        {squadron.badge_url && (
          <div style={{
            flexShrink: 0,
            width: 100,
            height: 100,
            borderRadius: 8,
            overflow: "hidden",
            border: "2px solid #e0dcd5",
            backgroundColor: "#f5f3ee",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={squadron.badge_url}
              alt={`${squadron.name} badge`}
              style={{ maxWidth: "90%", maxHeight: "90%", objectFit: "contain" }}
            />
          </div>
        )}
        <div>
          <h1 style={{
            fontFamily: "'Helvetica Neue', Arial, sans-serif",
            color: "#1a2332",
            fontSize: "2rem",
            marginBottom: "0.25rem",
            lineHeight: 1.2,
          }}>
            {squadron.name}
          </h1>
          {squadron.motto && (
            <p style={{
              fontFamily: "Georgia, serif",
              fontStyle: "italic",
              color: "#8b7355",
              fontSize: "1.1rem",
              marginBottom: "0.5rem",
            }}>
              &ldquo;{squadron.motto}&rdquo;
            </p>
          )}
          <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap", fontSize: "0.9rem", color: "#666" }}>
            {squadron.stations.length > 0 && (
              <span>Station: <strong style={{ color: "#1a2332" }}>{squadron.stations.join(", ")}</strong></span>
            )}
            <span>Memorials: <strong style={{ color: "#1a2332" }}>{squadron.memorials.length}</strong></span>
            {squadron.total_crew > 0 && (
              <span>Crew recorded: <strong style={{ color: "#1a2332" }}>{squadron.total_crew}</strong></span>
            )}
          </div>
        </div>
      </div>

      {/* Association link */}
      {squadron.association_url && (
        <div style={{
          backgroundColor: "#f5f3ee",
          border: "1px solid #e0dcd5",
          borderRadius: 8,
          padding: "1rem 1.25rem",
          marginBottom: "2rem",
          fontSize: "0.9rem",
        }}>
          <strong style={{ color: "#1a2332" }}>Squadron Association: </strong>
          <a
            href={squadron.association_url}
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: "#2c5f8a" }}
          >
            {squadron.association_url.replace(/^https?:\/\//, "").replace(/\/$/, "")}
          </a>
          <span style={{ color: "#999", marginLeft: "0.5rem" }}>↗</span>
        </div>
      )}

      {/* Map */}
      <h2 style={sectionStyle}>Memorial Locations</h2>
      <div style={{ marginBottom: "2rem" }}>
        <MemorialMap memorials={squadron.memorials} zoom={7} />
      </div>

      {/* Memorial list */}
      <h2 style={sectionStyle}>Memorials ({squadron.memorials.length})</h2>
      <div style={{ display: "grid", gap: "1rem", marginBottom: "2rem" }}>
        {squadron.memorials.map((m) => (
          <Link
            key={m.id}
            href={`/memorial/${m.id}`}
            style={{
              display: "block",
              padding: "1rem 1.25rem",
              backgroundColor: "#f9f8f5",
              border: "1px solid #e0dcd5",
              borderRadius: 8,
              textDecoration: "none",
              transition: "border-color 0.2s",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div>
                <h3 style={{
                  fontFamily: "'Helvetica Neue', Arial, sans-serif",
                  color: "#1a2332",
                  fontSize: "1rem",
                  marginBottom: "0.25rem",
                }}>
                  {m.title}
                </h3>
                <div style={{ fontSize: "0.85rem", color: "#666" }}>
                  {m.location_name && <span>{m.location_name}</span>}
                  {m.county && <span> · {m.county}</span>}
                </div>
                {m.crash_date && (
                  <div style={{ fontSize: "0.8rem", color: "#999", marginTop: "0.25rem" }}>
                    {m.crash_date}
                  </div>
                )}
              </div>
              <div style={{ textAlign: "right", flexShrink: 0 }}>
                {m.aircraft_type && (
                  <div style={{ fontSize: "0.8rem", color: "#8b7355", fontWeight: 600 }}>
                    {m.aircraft_type}
                  </div>
                )}
                {m.serial_number && (
                  <div style={{ fontSize: "0.75rem", color: "#999" }}>{m.serial_number}</div>
                )}
                {m.crew && m.crew.length > 0 && (
                  <div style={{ fontSize: "0.75rem", color: "#2c5f8a", marginTop: "0.25rem" }}>
                    {m.crew.length} crew
                  </div>
                )}
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Aircraft types */}
      {squadron.aircraft_types.length > 0 && (
        <>
          <h2 style={sectionStyle}>Aircraft Types</h2>
          <p style={{ color: "#444", lineHeight: 1.6, marginBottom: "2rem" }}>
            {squadron.aircraft_types.join(", ")}
          </p>
        </>
      )}
    </div>
  );
}
