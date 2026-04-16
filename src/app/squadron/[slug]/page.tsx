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
            {squadron.history?.nickname && (
              <span style={{ fontSize: "1rem", fontWeight: 400, color: "#8b7355", marginLeft: "0.5rem" }}>
                &ldquo;{squadron.history.nickname}&rdquo;
              </span>
            )}
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
          {squadron.history?.sub_units && squadron.history.sub_units.length > 0 && (
            <div style={{ fontSize: "0.85rem", color: "#666", marginTop: "0.5rem" }}>
              Squadrons: <strong style={{ color: "#1a2332" }}>{squadron.history.sub_units.join(" · ")}</strong>
            </div>
          )}
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
            {squadron.history?.aircraft_code && (
              <span style={{ color: "#999" }}> — Squadron code: <strong style={{ color: "#1a2332" }}>{squadron.history.aircraft_code}</strong></span>
            )}
          </p>
        </>
      )}

      {/* === ENRICHED CONTENT (from scraped data) === */}
      {squadron.history && (
        <>
          {/* Squadron History */}
          {squadron.history.summary && (
            <section style={{ marginBottom: "2.5rem" }}>
              <h2 style={sectionStyle}>Squadron History</h2>
              <p style={{ color: "#444", lineHeight: 1.8, fontSize: "0.95rem" }}>
                {squadron.history.summary}
              </p>
              {(squadron.history.total_sorties || squadron.history.killed) && (
                <div style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))",
                  gap: "1rem",
                  marginTop: "1.5rem",
                  padding: "1.25rem",
                  backgroundColor: "#f5f3ee",
                  borderRadius: 8,
                  border: "1px solid #e0dcd5",
                }}>
                  {squadron.history.total_operations && (
                    <div style={{ textAlign: "center" }}>
                      <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#1a2332" }}>{squadron.history.total_operations}</div>
                      <div style={{ fontSize: "0.75rem", color: "#8b7355", textTransform: "uppercase", letterSpacing: "0.05em" }}>Operations</div>
                    </div>
                  )}
                  {squadron.history.total_sorties && (
                    <div style={{ textAlign: "center" }}>
                      <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#1a2332" }}>{squadron.history.total_sorties.toLocaleString()}</div>
                      <div style={{ fontSize: "0.75rem", color: "#8b7355", textTransform: "uppercase", letterSpacing: "0.05em" }}>Sorties</div>
                    </div>
                  )}
                  {squadron.history.tons_dropped && (
                    <div style={{ textAlign: "center" }}>
                      <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#1a2332" }}>{squadron.history.tons_dropped.toLocaleString()}</div>
                      <div style={{ fontSize: "0.75rem", color: "#8b7355", textTransform: "uppercase", letterSpacing: "0.05em" }}>Tons dropped</div>
                    </div>
                  )}
                  {squadron.history.aircraft_lost && (
                    <div style={{ textAlign: "center" }}>
                      <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#1a2332" }}>{squadron.history.aircraft_lost}</div>
                      <div style={{ fontSize: "0.75rem", color: "#8b7355", textTransform: "uppercase", letterSpacing: "0.05em" }}>Aircraft lost</div>
                    </div>
                  )}
                  {squadron.history.killed && (
                    <div style={{ textAlign: "center" }}>
                      <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#1a2332" }}>{squadron.history.killed}</div>
                      <div style={{ fontSize: "0.75rem", color: "#8b7355", textTransform: "uppercase", letterSpacing: "0.05em" }}>Killed</div>
                    </div>
                  )}
                </div>
              )}
            </section>
          )}

          {/* Commanding Officers */}
          {squadron.history.commanding_officers && squadron.history.commanding_officers.length > 0 && (
            <section style={{ marginBottom: "2.5rem" }}>
              <h2 style={sectionStyle}>Commanding Officers</h2>
              <div style={{ display: "grid", gap: "0.75rem" }}>
                {squadron.history.commanding_officers.map((co, i) => (
                  <div key={i} style={{
                    padding: "0.75rem 1rem",
                    backgroundColor: "#f9f8f5",
                    border: "1px solid #e0dcd5",
                    borderRadius: 8,
                  }}>
                    <div style={{ fontWeight: 600, color: "#1a2332" }}>{co.name}</div>
                    <div style={{ fontSize: "0.8rem", color: "#666" }}>
                      {co.period}
                      {co.honours && <span style={{ color: "#8b7355" }}> — {co.honours}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Notable Personnel */}
          {squadron.history.notable_personnel && squadron.history.notable_personnel.length > 0 && (
            <section style={{ marginBottom: "2.5rem" }}>
              <h2 style={sectionStyle}>Notable Personnel</h2>
              <div style={{ display: "grid", gap: "1.25rem" }}>
                {squadron.history.notable_personnel.map((person, i) => (
                  <div key={i} style={{
                    padding: "1.25rem",
                    backgroundColor: "#f9f8f5",
                    border: "1px solid #e0dcd5",
                    borderRadius: 8,
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.5rem" }}>
                      <div>
                        <div style={{ fontWeight: 600, color: "#1a2332", fontSize: "1.05rem" }}>{person.name}</div>
                        {person.rank && <div style={{ fontSize: "0.8rem", color: "#666" }}>{person.rank}</div>}
                      </div>
                      <span style={{
                        fontSize: "0.75rem",
                        fontWeight: 600,
                        color: "#8b7355",
                        backgroundColor: "#f0ece2",
                        padding: "0.2rem 0.6rem",
                        borderRadius: 4,
                      }}>
                        {person.distinction}
                      </span>
                    </div>
                    {person.detail && (
                      <p style={{ color: "#444", lineHeight: 1.7, fontSize: "0.9rem", margin: 0 }}>
                        {person.detail}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Videos */}
          {squadron.history.videos && squadron.history.videos.length > 0 && (
            <section style={{ marginBottom: "2.5rem" }}>
              <h2 style={sectionStyle}>Videos</h2>
              <div style={{ display: "grid", gap: "1.5rem" }}>
                {squadron.history.videos.map((video, i) => {
                  const youtubeId = video.url.match(/(?:watch\?v=|embed\/)([^&?/]+)/)?.[1];
                  return (
                    <div key={i}>
                      {youtubeId && (
                        <div style={{
                          position: "relative",
                          paddingBottom: "56.25%",
                          height: 0,
                          overflow: "hidden",
                          borderRadius: 8,
                          border: "2px solid #e0dcd5",
                          marginBottom: "0.5rem",
                        }}>
                          <iframe
                            src={`https://www.youtube-nocookie.com/embed/${youtubeId}`}
                            title={video.title}
                            style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", border: "none" }}
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                            allowFullScreen
                            loading="lazy"
                          />
                        </div>
                      )}
                      <div style={{ fontSize: "0.85rem" }}>
                        <strong style={{ color: "#1a2332" }}>{video.title}</strong>
                        {video.source && <span style={{ color: "#999" }}> — {video.source}</span>}
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          )}

          {/* Books & References */}
          {squadron.history.books && squadron.history.books.length > 0 && (
            <section style={{ marginBottom: "2.5rem" }}>
              <h2 style={sectionStyle}>Books &amp; References</h2>
              <div style={{ display: "grid", gap: "0.75rem" }}>
                {squadron.history.books.map((book, i) => (
                  <div key={i} style={{
                    padding: "0.75rem 1rem",
                    backgroundColor: "#f9f8f5",
                    border: "1px solid #e0dcd5",
                    borderRadius: 8,
                  }}>
                    <div style={{ fontWeight: 600, color: "#1a2332", fontStyle: "italic" }}>{book.title}</div>
                    <div style={{ fontSize: "0.8rem", color: "#666" }}>
                      {book.author}
                      {book.year && ` (${book.year})`}
                      {book.isbn && <span style={{ color: "#999" }}> — ISBN: {book.isbn}</span>}
                    </div>
                    {book.notes && <div style={{ fontSize: "0.8rem", color: "#999", marginTop: "0.25rem" }}>{book.notes}</div>}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Source attribution */}
          {squadron.history.source_url && (
            <section style={{ marginBottom: "2rem" }}>
              <div style={{
                padding: "1rem 1.25rem",
                backgroundColor: "#f5f3ee",
                border: "1px solid #e0dcd5",
                borderRadius: 8,
                fontSize: "0.85rem",
                color: "#666",
              }}>
                Squadron history sourced from{" "}
                <a href={squadron.history.source_url} target="_blank" rel="noopener noreferrer" style={{ color: "#2c5f8a" }}>
                  {squadron.history.source_name || squadron.history.source_url.replace(/^https?:\/\//, "").replace(/\/$/, "")}
                </a>
                . All content is attributed to the original authors and used with respect for their research.
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
