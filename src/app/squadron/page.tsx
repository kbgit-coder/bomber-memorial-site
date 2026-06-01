import { Metadata } from "next";
import { getAllSquadrons, SquadronCategory } from "@/lib/squadrons";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Squadrons | Bomber Command Memorial Register",
  description:
    "Browse memorials by squadron. Squadrons and bomb groups linked to multiple memorial sites across the Bomber Command Memorial Register.",
};

export default function SquadronsPage() {
  const squadrons = getAllSquadrons();

  // Group by category (already sorted by category then number)
  const categories: { label: SquadronCategory; description: string }[] = [
    { label: 'RAF Bomber Command', description: 'Operational squadrons of RAF Bomber Command and allied air forces' },
    { label: 'USAAF Bomb Groups', description: 'United States Army Air Forces bomb groups based in Britain' },
    { label: 'Training Units', description: 'Operational Training Units, Heavy Conversion Units, and finishing schools' },
    { label: 'Other Units', description: 'Other units and commands' },
  ];

  const grouped = new Map<SquadronCategory, typeof squadrons>();
  for (const sq of squadrons) {
    const list = grouped.get(sq.category) || [];
    list.push(sq);
    grouped.set(sq.category, list);
  }

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "2rem 1.5rem" }}>
      <nav style={{ marginBottom: "1.5rem", fontSize: "0.85rem" }}>
        <Link href="/" style={{ color: "#7a4500" }}>Home</Link>
        <span style={{ color: "#999", margin: "0 0.5rem" }}>/</span>
        <span style={{ color: "#999" }}>Squadrons</span>
      </nav>

      <h1 style={{
        fontFamily: "'Helvetica Neue', Arial, sans-serif",
        color: "#1a2332",
        fontSize: "2rem",
        marginBottom: "0.5rem",
        lineHeight: 1.2,
      }}>
        Squadrons &amp; Units
      </h1>
      <p style={{ color: "#666", marginBottom: "2rem", fontSize: "0.95rem", lineHeight: 1.6 }}>
        {squadrons.length} squadrons, bomb groups, and training units linked to multiple memorial sites.
        Select a unit to see its memorials, locations, and crew records.
      </p>

      {categories.map((cat) => {
        const items = grouped.get(cat.label);
        if (!items || items.length === 0) return null;
        return (
          <section key={cat.label} style={{ marginBottom: "2.5rem" }}>
            <h2 style={{
              fontFamily: "'Helvetica Neue', Arial, sans-serif",
              color: "#1a2332",
              fontSize: "1.25rem",
              marginBottom: "0.25rem",
              paddingBottom: "0.5rem",
              borderBottom: "2px solid #e0dcd5",
            }}>
              {cat.label}
            </h2>
            <p style={{ color: "#999", fontSize: "0.8rem", marginBottom: "1rem" }}>
              {cat.description}
            </p>
            <div style={{ display: "grid", gap: "0.5rem" }}>
              {items.map((sq) => (
                <Link
                  key={sq.slug}
                  href={`/squadron/${sq.slug}`}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "1rem",
                    padding: "0.75rem 1rem",
                    backgroundColor: "#f9f8f5",
                    border: "1px solid #e0dcd5",
                    borderRadius: 8,
                    textDecoration: "none",
                  }}
                >
                  {sq.badge_url ? (
                    <div style={{
                      width: 40,
                      height: 40,
                      flexShrink: 0,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}>
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={sq.badge_url}
                        alt=""
                        style={{ maxWidth: 36, maxHeight: 36, objectFit: "contain" }}
                      />
                    </div>
                  ) : (
                    <div style={{
                      width: 40,
                      height: 40,
                      flexShrink: 0,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      backgroundColor: "#e0dcd5",
                      borderRadius: 4,
                      fontSize: "0.7rem",
                      color: "#8b7355",
                    }}>
                      {sq.sort_number < 9999 ? sq.sort_number : "—"}
                    </div>
                  )}
                  <div style={{ flex: 1 }}>
                    <div style={{
                      fontFamily: "'Helvetica Neue', Arial, sans-serif",
                      color: "#1a2332",
                      fontWeight: 600,
                      fontSize: "0.95rem",
                    }}>
                      {sq.name}
                    </div>
                    {sq.motto && (
                      <div style={{ fontSize: "0.8rem", color: "#8b7355", fontStyle: "italic" }}>
                        &ldquo;{sq.motto}&rdquo;
                      </div>
                    )}
                    {sq.stations.length > 0 && (
                      <div style={{ fontSize: "0.75rem", color: "#999" }}>
                        {sq.stations.join(", ")}
                      </div>
                    )}
                  </div>
                  <div style={{ textAlign: "right", flexShrink: 0, fontSize: "0.85rem", color: "#666" }}>
                    <div><strong style={{ color: "#1a2332" }}>{sq.memorials.length}</strong> memorials</div>
                    {sq.total_crew > 0 && (
                      <div style={{ fontSize: "0.75rem" }}>{sq.total_crew} crew</div>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
