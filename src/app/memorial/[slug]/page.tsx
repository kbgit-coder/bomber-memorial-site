import { Metadata } from "next";
import Linkify from "@/components/Linkify";
import {
  getAllMemorialSlugs,
  getMemorialBySlug,
  getNearbyMemorials,
  getRelatedMemorials,
} from "@/lib/data";
import { getStoriesForMemorial } from "@/lib/stories";
import { getSquadronSlugForName } from "@/lib/squadrons";
import CrewTable from "@/components/CrewTable";
import StubCTA from "@/components/StubCTA";
import MemorialMap from "@/components/MemorialMap";
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

  const description = memorial.narrative
    ? memorial.narrative.slice(0, 155) + "..."
    : memorial.crew_summary
    ? memorial.crew_summary.slice(0, 155) + "..."
    : `${memorial.title} - Bomber Command Memorial Register`;

  return {
    title: `${memorial.title} | Bomber Command Memorial Register`,
    description,
    openGraph: {
      title: memorial.title,
      description,
      type: "article",
      url: `https://bombermemorial.co.uk/memorial/${params.slug}`,
    },
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
        <Link href="/" style={{ color: "#7a4500" }}>Return to the Register</Link>
      </div>
    );
  }

  // Convert ALL CAPS inscription text to readable title case
  // Processes per-sentence so mixed-case inscriptions (part ALL CAPS, part normal) are handled correctly
  function smartTitleCase(text: string): string {
    const lowercase = new Set(['a','an','the','and','but','or','for','nor','of','to','in','on','at','by','with','from','as','into','upon','per','via']);
    const keepUpper = new Set(['RAF','RCAF','RAAF','RNZAF','DFC','DFM','DSO','OBE','MBE','CGM','AFC','USA','USAAF','VR','OTU','HCU','LFS','WW2','WWII','SQN','SQDN','AMDG']);

    function convertSegment(segment: string): string {
      const letters = segment.replace(/[^a-zA-Z]/g, '');
      // Only convert segments that are mostly uppercase (>60% uppercase letters)
      if (!letters || letters.length < 4) return segment;
      const upperCount = letters.replace(/[a-z]/g, '').length;
      if (upperCount / letters.length < 0.6) return segment; // Already mixed/lowercase — leave it

      const words = segment.split(/(\s+)/); // preserve whitespace
      return words.map((word, i) => {
        if (/^\s+$/.test(word)) return word; // whitespace
        const stripped = word.replace(/[^a-zA-Z]/g, '').toUpperCase();
        if (keepUpper.has(stripped)) return word;
        if (/^[IVXLCDM]+$/.test(stripped) && stripped.length <= 5 && stripped.length > 0) return word;
        if (/\d/.test(word)) return word.replace(/(\d+)(ST|ND|RD|TH)/g, (_, n, s) => n + s.toLowerCase());
        if (/^\[/.test(word)) return word;
        const lower = word.toLowerCase();
        if (i === 0) return word.charAt(0).toUpperCase() + lower.slice(1);
        if (lowercase.has(lower)) return lower;
        return word.charAt(0).toUpperCase() + lower.slice(1);
      }).join('');
    }

    // Split on sentence boundaries (period + space, or where case transitions from ALL CAPS to mixed)
    const segments = text.split(/(?<=\.\s)/);
    return segments.map(s => convertSegment(s)).join('');
  }

  const qualityColour = {
    Comprehensive: { bg: "#2d5016", text: "#a8d48c", label: "COMPREHENSIVE RECORD" },
    Partial: { bg: "#5a4a1e", text: "#d4c98c", label: "PARTIAL RECORD" },
    Stub: { bg: "#5a3a1e", text: "#d4a88c", label: "STUB RECORD" },
  };
  const badge = qualityColour[memorial.data_quality as keyof typeof qualityColour] || qualityColour["Stub"];

  // Related stories
  const relatedStories = getStoriesForMemorial(params.slug);

  // Related memorials (same incident, different page)
  const relatedMemorials = getRelatedMemorials(params.slug);

  // Nearby memorials (only when we have coordinates)
  const nearbyMemorials =
    memorial.latitude != null && memorial.longitude != null
      ? getNearbyMemorials(memorial.latitude, memorial.longitude, params.slug)
      : [];

  // Location confidence badge config
  const lc = memorial.location_confidence;
  // Support both 'status' (actual data) and 'level' (legacy spec field)
  const lcStatus = lc?.status ?? lc?.level;
  const lcBadge = lcStatus === 'confirmed' || lcStatus === 'verified'
    ? { bg: '#1a4a1a', text: '#7ecb7e', label: 'Verified Location' }
    : lcStatus === 'approximate'
    ? { bg: '#4a3800', text: '#d4b84a', label: 'Approximate Location' }
    : lcStatus === 'estimated'
    ? { bg: '#4a1a1a', text: '#d47e7e', label: 'Estimated Location' }
    : null;

  // Show full_narrative for all records — enriched records should show MORE, not less
  const fullNarratives = (memorial.external_narratives || []).filter(n => n.full_narrative);

  // JSON-LD structured data for this memorial
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "HistoricalEvent",
    "name": memorial.title,
    "description": memorial.narrative || memorial.crew_summary || `${memorial.title} — Bomber Command Memorial Register`,
    "url": `https://bombermemorial.co.uk/memorial/${params.slug}`,
    ...(memorial.crash_date && { "startDate": memorial.crash_date }),
    ...(memorial.latitude != null && memorial.longitude != null && {
      "location": {
        "@type": "Place",
        "name": memorial.location_name || memorial.title,
        "geo": {
          "@type": "GeoCoordinates",
          "latitude": memorial.latitude,
          "longitude": memorial.longitude,
        },
        ...(memorial.county && { "address": { "@type": "PostalAddress", "addressRegion": memorial.county, "addressCountry": memorial.country || "United Kingdom" } }),
      },
    }),
    "isPartOf": {
      "@type": "Dataset",
      "name": "Bomber Command Memorial Register",
      "url": "https://bombermemorial.co.uk",
    },
  };

  const breadcrumbLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://bombermemorial.co.uk" },
      ...(memorial.country ? [{ "@type": "ListItem", "position": 2, "name": memorial.country, "item": `https://bombermemorial.co.uk/region/${memorial.country.toLowerCase().replace(/\s+/g, "-")}` }] : []),
      { "@type": "ListItem", "position": memorial.country ? 3 : 2, "name": memorial.title },
    ],
  };

  return (
    <div data-pagefind-body="" style={{ maxWidth: 900, margin: "0 auto", padding: "2rem 1.5rem" }}>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbLd) }} />
      {/* Breadcrumb */}
      <nav style={{ marginBottom: "1.5rem", fontSize: "0.85rem" }}>
        <Link href="/" style={{ color: "#7a4500" }}>Home</Link>
        <span style={{ color: "#999", margin: "0 0.5rem" }}>/</span>
        {memorial.country && (
          <>
            <Link
              href={`/region/${memorial.country.toLowerCase().replace(/\s+/g, "-")}`}
              style={{ color: "#7a4500" }}
            >
              {memorial.country}
            </Link>
            <span style={{ color: "#999", margin: "0 0.5rem" }}>/</span>
          </>
        )}
        <span style={{ color: "#999" }}>{memorial.title}</span>
      </nav>

      {/* Title */}
      <h1 data-pagefind-meta="title" style={h1Style}>{memorial.title}</h1>


      {/* Pagefind filter metadata — hidden spans for faceted search */}
      {memorial.squadron && (
        <span data-pagefind-filter="squadron" style={{display:'none'}}>{memorial.squadron}</span>
      )}
      {memorial.county && (
        <span data-pagefind-filter="county" style={{display:'none'}}>{memorial.county}</span>
      )}
      {memorial.aircraft_type && (
        <span data-pagefind-filter="aircraft" style={{display:'none'}}>{memorial.aircraft_type}</span>
      )}

      {/* Memorial name (e.g. "The Black Swan Memorial") */}
      {memorial.memorial_name && (
        <p style={{ fontSize: "1.15rem", color: "#8b7355", fontStyle: "italic", marginBottom: "0.25rem" }}>
          {memorial.memorial_name}
        </p>
      )}

      {memorial.location_name && (
        <p style={{ fontSize: "1.1rem", color: "#666", marginBottom: "0.5rem" }}>
          {memorial.location_name}
        </p>
      )}

      {/* Quality badge */}
      <div style={{ marginBottom: "2rem" }}>
        <span style={{
          fontSize: "0.75rem",
          padding: "0.25rem 0.75rem",
          borderRadius: 12,
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
          textTransform: "uppercase",
          letterSpacing: "0.05em",
          backgroundColor: badge.bg,
          color: badge.text,
        }}>
          <span data-pagefind-filter="quality">{memorial.data_quality || "Stub"}</span> Record
        </span>
      </div>

      {/* Photos */}
      {memorial.photos && memorial.photos.length > 0 && (
        <section style={{ marginBottom: "2.5rem" }} aria-label="Photograph gallery">
          <h2 style={sectionHeading}>Photographs</h2>
          <div style={{
            display: "grid",
            gridTemplateColumns: `repeat(auto-fill, minmax(${memorial.photos.length === 1 ? "400px" : "200px"}, 1fr))`,
            gap: "1rem",
          }}>
            {memorial.photos.map((photo, i) => (
              <figure key={i} style={{ margin: 0 }}>
                <div style={{
                  borderRadius: 8,
                  overflow: "hidden",
                  border: "1px solid #e0dcd5",
                  position: "relative",
                  aspectRatio: "4/3",
                }}>
                  <Image
                    src={`/images/memorials/${photo.filename}`}
                    alt={photo.caption || `${memorial.title} - photograph ${i + 1}`}
                    fill
                    style={{ objectFit: "contain" }}
                    sizes="(max-width: 600px) 100vw, 400px"
                    unoptimized
                  />
                </div>
                {(() => {
                  // Only show caption if it's meaningful (not a filename derivative)
                  const isJunkCaption = photo.caption && (
                    /[_]/.test(photo.caption) ||
                    /w\d{3,4}/.test(photo.caption) ||
                    /\d{3,4}x\d{3,4}/.test(photo.caption) ||
                    /\.(jpg|jpeg|png)/i.test(photo.caption) ||
                    /^[a-f0-9]{10,}/.test(photo.caption)
                  );
                  const caption = isJunkCaption ? null : photo.caption;
                  const hasContent = caption || photo.credit || photo.source || photo.date_taken;
                  if (!hasContent) return null;
                  return (
                    <figcaption style={{ fontSize: "0.8rem", color: "#666", marginTop: "0.5rem", fontStyle: "italic" }}>
                      {caption && <span>{caption}</span>}
                      {(photo.credit || photo.source || photo.date_taken) && (
                        <span style={{ color: "#999" }}>
                          {caption && " — "}
                          {photo.credit && <>Credit: {photo.credit}</>}
                          {photo.source && !photo.credit && <>Source: {photo.source}</>}
                          {photo.date_taken && <> ({photo.date_taken})</>}
                        </span>
                      )}
                    </figcaption>
                  );
                })()}
              </figure>
            ))}
          </div>
        </section>
      )}

      {/* The Memorial */}
      {(() => {
        const parts: string[] = [];
        const hasStructuredInfo = memorial.memorial_type || memorial.erected_by || memorial.dedication_date;
        const formatDate = (d: string) => {
          const m = d.match(/^(\d{4})-(\d{2})-(\d{2})$/);
          if (!m) return d;
          const months = ["January","February","March","April","May","June","July","August","September","October","November","December"];
          return `${parseInt(m[3])} ${months[parseInt(m[2])-1]} ${m[1]}`;
        };
        const dedDate = memorial.dedication_date ? formatDate(memorial.dedication_date) : "";
        if (hasStructuredInfo) {
          const typeStr = memorial.memorial_type ? memorial.memorial_type.toLowerCase() : "memorial";
          if (memorial.erected_by && dedDate) {
            parts.push(`This ${typeStr} was erected by ${memorial.erected_by} and dedicated on ${dedDate}.`);
          } else if (memorial.erected_by) {
            parts.push(`This ${typeStr} was erected by ${memorial.erected_by}.`);
          } else if (dedDate) {
            parts.push(`This ${typeStr} was dedicated on ${dedDate}.`);
          }
        }
        if (memorial.maintainer?.notes) {
          parts.push(memorial.maintainer.notes);
        } else if (memorial.maintainer?.organisation && memorial.maintainer.organisation !== memorial.erected_by) {
          parts.push(`It is maintained by ${memorial.maintainer.organisation}.`);
        }
        if (memorial.condition && memorial.condition.toLowerCase() !== "unknown") {
          parts.push(`The memorial is in ${memorial.condition.toLowerCase()} condition.`);
        }
        const connectionText = parts.join(" ");
        const showSection = connectionText || memorial.memorial_type || memorial.erected_by || memorial.dedication_date || memorial.condition || memorial.inscription;
        if (!showSection) return null;
        return (
          <section style={{ marginBottom: "2.5rem" }}>
            <h2 style={sectionHeading}>The Memorial</h2>
            {connectionText && (
              <p style={{ fontSize: "0.95rem", color: "#444", lineHeight: 1.8, marginBottom: "1.5rem" }}>
                {connectionText}
              </p>
            )}
            {(memorial.memorial_type || memorial.erected_by || memorial.dedication_date || memorial.condition) && (
              <div style={{ ...cardBox, display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "1rem" }}>
                {memorial.memorial_type && <DetailItem label="Type" value={memorial.memorial_type} />}
                {memorial.erected_by && <DetailItem label="Erected By" value={memorial.erected_by} />}
                {memorial.dedication_date && <DetailItem label="Dedication Date" value={dedDate || memorial.dedication_date} />}
                {memorial.condition && <DetailItem label="Condition" value={memorial.condition} />}
              </div>
            )}
            {(() => {
              const insc = memorial.inscription;
              if (!insc) {
                // No inscription — show CTA
                return (
                  <div style={{
                    marginTop: "1.5rem",
                    padding: "1.25rem 1.5rem",
                    backgroundColor: "#f8f6f2",
                    borderLeft: "4px solid #8b7355",
                    borderRadius: "0 8px 8px 0",
                    fontFamily: "Georgia, 'Times New Roman', serif",
                  }}>
                    <div style={{
                      fontSize: "0.75rem",
                      color: "#8b7355",
                      textTransform: "uppercase",
                      letterSpacing: "0.1em",
                      fontFamily: "'Helvetica Neue', Arial, sans-serif",
                      marginBottom: "0.75rem",
                      fontWeight: 600,
                    }}>
                      Inscription
                    </div>
                    <p style={{
                      fontSize: "0.95rem",
                      color: "#666",
                      lineHeight: 1.8,
                      fontStyle: "italic",
                      marginBottom: 0,
                    }}>
                      Could you help us fill in the inscription?
                    </p>
                  </div>
                );
              }

              // If inscription contains crew names that are already in the crew section,
              // show a condensed version noting the names are listed on the memorial
              const crewNames = (memorial.crew || []).map(c => c.name?.split(" ").pop()?.toLowerCase()).filter(Boolean);
              const nameMatches = crewNames.filter(surname => surname && surname.length > 3 && insc.toLowerCase().includes(surname));
              const hasCrewList = nameMatches.length >= 3;

              // Split inscription: everything before the first crew name, and a note about the rest
              let displayText = insc;
              let crewNote = "";
              if (hasCrewList) {
                // Find where crew names start and show preamble + note
                const lines = insc.split(/\n/);
                const preambleLines: string[] = [];
                let foundCrew = false;
                for (const line of lines) {
                  const lineHasCrew = crewNames.some(s => s && s.length > 3 && line.toLowerCase().includes(s));
                  if (lineHasCrew && !foundCrew) {
                    foundCrew = true;
                  }
                  if (!foundCrew) {
                    preambleLines.push(line);
                  }
                }
                if (foundCrew && preambleLines.length > 0) {
                  displayText = preambleLines.join("\n").trim();
                  crewNote = `The names of all ${memorial.crew?.length || "the"} crew members are inscribed on the memorial.`;
                } else if (foundCrew) {
                  displayText = "";
                  crewNote = `The memorial inscription lists the names of all ${memorial.crew?.length || "the"} crew members.`;
                }
              }

              return (
                <div style={{
                  marginTop: "1.5rem",
                  padding: "1.25rem 1.5rem",
                  backgroundColor: "#f8f6f2",
                  borderLeft: "4px solid #8b7355",
                  borderRadius: "0 8px 8px 0",
                  fontFamily: "Georgia, 'Times New Roman', serif",
                }}>
                  <div style={{
                    fontSize: "0.75rem",
                    color: "#8b7355",
                    textTransform: "uppercase",
                    letterSpacing: "0.1em",
                    fontFamily: "'Helvetica Neue', Arial, sans-serif",
                    marginBottom: "0.75rem",
                    fontWeight: 600,
                  }}>
                    Inscription
                  </div>
                  {displayText && (
                    <div style={{
                      fontSize: "0.95rem",
                      color: "#333",
                      lineHeight: 1.8,
                      fontStyle: "italic",
                    }}>
                      {smartTitleCase(displayText
                        .replace(/\n+/g, " ")
                        .replace(/\s*\/\s*/g, " ")
                        .replace(/\s+/g, " ")
                        .trim())
                        .replace(/\(NAMES?\)/gi, "[crew names listed on memorial]")
                        .replace(/\(Halfpint\)/gi, "")
                        .replace(/\(Sic\)/gi, "[sic]")
                        .replace(/\(Hons\)/gi, "(Hons)")}
                    </div>
                  )}
                  {crewNote && (
                    <p style={{
                      fontSize: "0.85rem",
                      color: "#666",
                      fontStyle: "normal",
                      marginTop: displayText ? "0.75rem" : 0,
                      marginBottom: 0,
                    }}>
                      {crewNote}
                    </p>
                  )}
                </div>
              );
            })()}
          </section>
        );
      })()}

      {/* Location Map */}
      {memorial.latitude != null && memorial.longitude != null && (
        <section style={{ marginBottom: "2.5rem" }}>
          <h2 style={{ ...sectionHeading, display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
            Location
            {lcBadge && (
              <span aria-label={`Location confidence: ${lcBadge.label}`} style={{
                fontSize: "0.7rem",
                padding: "0.2rem 0.65rem",
                borderRadius: 10,
                fontFamily: "'Helvetica Neue', Arial, sans-serif",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                backgroundColor: lcBadge.bg,
                color: lcBadge.text,
                fontWeight: 600,
              }}>
                {lcBadge.label}
              </span>
            )}
          </h2>
          {memorial.memorial_address && (
            <p style={{ color: "#333", fontSize: "0.95rem", marginBottom: "0.5rem" }}>
              {memorial.memorial_address}
            </p>
          )}
          {memorial.location_name && !memorial.memorial_address && (
            <p style={{ color: "#666", fontSize: "0.95rem", marginBottom: "0.5rem" }}>
              {memorial.location_name}
              {memorial.county && `, ${memorial.county}`}
            </p>
          )}
          {memorial.memorial_access_notes && (
            <p style={{
              color: "#666",
              fontSize: "0.9rem",
              marginBottom: "1rem",
              fontStyle: "italic",
              backgroundColor: "#f8f6f2",
              padding: "0.75rem 1rem",
              borderRadius: 6,
              borderLeft: "3px solid #8b7355",
            }}>
              {memorial.memorial_access_notes}
            </p>
          )}
          <div aria-label={`Map showing location of ${memorial.title}`} role="region">
            <MemorialMap
              memorials={[memorial]}
              center={[memorial.latitude, memorial.longitude]}
              zoom={13}
            />
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem 2rem", marginTop: "0.75rem" }}>
            {memorial.what3words && (
              <p style={{ fontSize: "0.9rem", margin: 0 }}>
                <span style={{ color: "#999" }}>what3words: </span>
                <a
                  href={`https://what3words.com/${memorial.what3words}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: "#7a4500", fontWeight: 500 }}
                >
                  {"///"}{memorial.what3words}
                </a>
              </p>
            )}
            {memorial.os_grid_reference && (
              <p style={{ fontSize: "0.9rem", margin: 0 }}>
                <span style={{ color: "#999" }}>OS Grid Ref: </span>
                <span style={{ fontWeight: 500, color: "#333", fontFamily: "'Helvetica Neue', Arial, sans-serif" }}>
                  {memorial.os_grid_reference}
                </span>
              </p>
            )}
          </div>
        </section>
      )}

      {/* What Happened — always shown; empty state invites community contributions */}
      <section style={{ marginBottom: "2.5rem" }}>
        <h2 style={sectionHeading}>What Happened</h2>
        {memorial.narrative ? (
          <div style={narrativeBox}>
            {memorial.narrative.split('\n\n').map((para, i) => (
              <p key={i} style={{ marginBottom: i < memorial.narrative!.split('\n\n').length - 1 ? '1rem' : 0 }}><Linkify text={para} /></p>
            ))}
          </div>
        ) : (
          <div style={{
            ...narrativeBox,
            borderLeft: "3px solid #c9b98a",
            backgroundColor: "#faf8f4",
          }}>
            <p style={{ color: "#8b7355", fontStyle: "italic", marginBottom: "0.75rem", lineHeight: 1.7 }}>
              Do you have information about this crew or memorial? We&apos;d love to hear from you — your knowledge helps keep these stories alive for future generations.
            </p>
            <a
              href={`mailto:admin@bombermemorial.co.uk?subject=Contribution%3A%20${encodeURIComponent(memorial.title)}&body=Memorial%3A%20${encodeURIComponent(memorial.title)}%0APage%3A%20https%3A%2F%2Fbombermemorial.co.uk%2Fmemorial%2F${params.slug}%0A%0APlease%20share%20what%20you%20know%3A%0A%0A`}
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
              Contribute to this memorial
            </a>
          </div>
        )}
      </section>

      {/* Community Connection — moved up for human story flow */}
      <section style={{ marginBottom: "2.5rem" }}>
        <h2 style={sectionHeading}>Community Connection</h2>
        {memorial.community_connection ? (
          <div style={narrativeBox}>
            {memorial.community_connection.split('\n\n').map((para, i) => (
              <p key={i} style={{ marginBottom: i < memorial.community_connection!.split('\n\n').length - 1 ? '1rem' : 0 }}><Linkify text={para} /></p>
            ))}
          </div>
        ) : (
          <div style={{
            backgroundColor: "#f8f6f2",
            border: "1px solid #e0dcd5",
            borderRadius: 8,
            padding: "1.25rem 1.5rem",
            textAlign: "center",
          }}>
            <p style={{ fontSize: "0.95rem", color: "#555", marginBottom: "0.75rem", lineHeight: 1.6 }}>
              Every memorial has a story — why it was built, who campaigned for it, and what it means to the local community.
              If you know the story behind this memorial, we would love to hear it.
            </p>
            <a
              href={`mailto:admin@bombermemorial.co.uk?subject=Community%20story%3A%20${encodeURIComponent(memorial.title)}&body=Memorial%3A%20${encodeURIComponent(memorial.title)}%0APage%3A%20https%3A%2F%2Fbombermemorial.co.uk%2Fmemorial%2F${params.slug}%0A%0APlease%20tell%20us%20the%20story%20behind%20this%20memorial%20%E2%80%94%20why%20it%20was%20built%2C%20who%20was%20involved%2C%20and%20what%20it%20means%20to%20the%20local%20community%3A%0A%0A`}
              style={{
                display: "inline-block",
                padding: "0.5rem 1.25rem",
                backgroundColor: "#1a2332",
                color: "#c9b98a",
                borderRadius: 6,
                fontSize: "0.85rem",
                fontFamily: "'Helvetica Neue', Arial, sans-serif",
                textDecoration: "none",
              }}
            >
              Share this memorial&apos;s story
            </a>
          </div>
        )}
      </section>

      {/* Related Stories */}
      {relatedStories.length > 0 && (
        <section style={{ marginBottom: "2.5rem" }}>
          <h2 style={sectionHeading}>
            {relatedStories.length === 1 ? "Story" : "Stories"}
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {relatedStories.map((story) => (
              <Link
                key={story.slug}
                href={`/stories/${story.slug}`}
                style={{ textDecoration: "none", color: "inherit" }}
              >
                <div style={{
                  backgroundColor: "#f8f6f2",
                  borderLeft: "4px solid #8b7355",
                  borderRadius: "0 8px 8px 0",
                  padding: "1.25rem 1.5rem",
                }}>
                  <div style={{
                    fontFamily: "'Helvetica Neue', Arial, sans-serif",
                    color: "#1a2332",
                    fontSize: "1rem",
                    fontWeight: 600,
                    marginBottom: "0.25rem",
                  }}>
                    {story.title}
                  </div>
                  {story.subtitle && (
                    <div style={{ fontSize: "0.9rem", color: "#8b7355", fontStyle: "italic", marginBottom: "0.5rem" }}>
                      {story.subtitle}
                    </div>
                  )}
                  <div style={{ fontSize: "0.85rem", color: "#666", lineHeight: 1.5, marginBottom: "0.5rem" }}>
                    {story.summary.length > 200 ? story.summary.slice(0, 200) + "..." : story.summary}
                  </div>
                  <div style={{ fontSize: "0.8rem", color: "#7a4500", fontWeight: 600, fontFamily: "'Helvetica Neue', Arial, sans-serif" }}>
                    Read the full story &rarr;
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Documents / Downloads */}
      {memorial.documents && memorial.documents.length > 0 && (
        <section style={{ marginBottom: "2.5rem" }}>
          <h2 style={sectionHeading}>Documents</h2>
          <div style={cardBox}>
            {memorial.documents.map((doc, i) => (
              <div key={i} style={{
                display: "flex",
                alignItems: "flex-start",
                gap: "1rem",
                padding: "1rem",
                backgroundColor: i % 2 === 0 ? "#faf8f4" : "#ffffff",
                borderRadius: 6,
                marginBottom: i < memorial.documents!.length - 1 ? "0.5rem" : 0,
              }}>
                <div style={{
                  flexShrink: 0,
                  width: 40,
                  height: 40,
                  backgroundColor: "#1a2332",
                  borderRadius: 6,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#c9b98a",
                  fontSize: "0.75rem",
                  fontWeight: 700,
                }}>PDF</div>
                <div style={{ flex: 1 }}>
                  <a
                    href={`/${doc.filename}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ color: "#1a2332", fontWeight: 600, fontSize: "0.95rem", textDecoration: "none" }}
                  >
                    {doc.title}
                  </a>
                  {doc.description && (
                    <p style={{ fontSize: "0.85rem", color: "#666", marginTop: "0.25rem", lineHeight: 1.5 }}>
                      {doc.description}
                    </p>
                  )}
                  {(doc.author || doc.pages) && (
                    <p style={{ fontSize: "0.8rem", color: "#999", marginTop: "0.25rem" }}>
                      {doc.author && <span>{doc.author}</span>}
                      {doc.author && doc.pages && <span> · </span>}
                      {doc.pages && <span>{doc.pages} pages</span>}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Remembrance — moved up for human story flow */}
      {(() => {
        const r = memorial.remembrance;
        const hasRemembranceData = r && (r.annual_service || r.service_description || (r.events && r.events.length > 0));

        return (
          <section style={{ marginBottom: "2.5rem" }}>
            <h2 style={sectionHeading}>Remembrance</h2>
            {hasRemembranceData ? (
              <div style={cardBox}>
                {r!.service_description && (
                  <p style={{ fontSize: "0.95rem", color: "#333", lineHeight: 1.7, marginBottom: "0.75rem" }}>
                    {r!.service_description}
                  </p>
                )}
                {r!.annual_service && r!.service_date && !r!.service_description && (
                  <p style={{ fontSize: "0.95rem", color: "#333", lineHeight: 1.7, marginBottom: "0.75rem" }}>
                    An annual commemorative service is held on {r!.service_date}.
                  </p>
                )}
                {r!.events && r!.events.length > 0 && (
                  <div style={{ marginTop: "0.75rem" }}>
                    {r!.events.map((event, i) => (
                      <div key={i} style={{
                        padding: "0.75rem 1rem",
                        backgroundColor: "#f8f6f2",
                        borderLeft: "3px solid #c9b98a",
                        borderRadius: "0 6px 6px 0",
                        marginBottom: "0.5rem",
                      }}>
                        <div style={{ fontWeight: 600, color: "#1a2332", fontSize: "0.95rem" }}>
                          {event.name}
                          {event.date && (
                            <span style={{ fontWeight: 400, color: "#666", marginLeft: "0.5rem", fontSize: "0.85rem" }}>
                              ({event.date})
                            </span>
                          )}
                        </div>
                        {event.description && (
                          <p style={{ fontSize: "0.9rem", color: "#555", marginTop: "0.25rem", lineHeight: 1.6, marginBottom: 0 }}>
                            {event.description}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
                {r!.last_known_event && (
                  <p style={{ fontSize: "0.8rem", color: "#999", marginTop: "0.5rem", marginBottom: 0 }}>
                    Last known event: {r!.last_known_event}
                  </p>
                )}
              </div>
            ) : (
              <div style={{
                backgroundColor: "#f8f6f2",
                border: "1px solid #e0dcd5",
                borderRadius: 8,
                padding: "1.25rem 1.5rem",
                textAlign: "center",
              }}>
                <p style={{ fontSize: "0.95rem", color: "#555", marginBottom: "0.75rem", lineHeight: 1.6 }}>
                  Do you know of any commemorative events or annual services held at this memorial?
                  We would love to hear from local communities who remember.
                </p>
                <a
                  href={`mailto:admin@bombermemorial.co.uk?subject=Remembrance%20information%3A%20${encodeURIComponent(memorial.title)}&body=Memorial%3A%20${encodeURIComponent(memorial.title)}%0APage%3A%20https%3A%2F%2Fbombermemorial.co.uk%2Fmemorial%2F${params.slug}%0A%0APlease%20tell%20us%20about%20any%20commemorative%20events%20or%20annual%20services%20held%20at%20this%20memorial%3A%0A%0A`}
                  style={{
                    display: "inline-block",
                    padding: "0.5rem 1.25rem",
                    backgroundColor: "#1a2332",
                    color: "#c9b98a",
                    borderRadius: 6,
                    fontSize: "0.85rem",
                    fontFamily: "'Helvetica Neue', Arial, sans-serif",
                    textDecoration: "none",
                  }}
                >
                  Share remembrance information
                </a>
              </div>
            )}
          </section>
        );
      })()}

      {/* Aircraft Details */}
      {(memorial.aircraft_type || memorial.serial_number || memorial.squadron || memorial.station) && (
        <section style={{ marginBottom: "2.5rem" }}>
          <h2 style={sectionHeading}>Aircraft &amp; Operation Details</h2>
          <div style={detailGrid}>
            {memorial.squadron_badge_url && (() => {
              const sqSlug = memorial.squadron ? getSquadronSlugForName(memorial.squadron) : undefined;
              const badge = (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", minWidth: 100, padding: "0.5rem" }}>
                  <Image
                    src={memorial.squadron_badge_url}
                    alt={`${memorial.squadron || 'Squadron'} badge`}
                    width={80}
                    height={80}
                    style={{ objectFit: "contain" }}
                    unoptimized
                  />
                  {memorial.squadron_motto && (
                    <span style={{ fontSize: "0.7rem", color: "#8b7355", fontStyle: "italic", marginTop: "0.4rem", textAlign: "center" }}>
                      {memorial.squadron_motto}
                    </span>
                  )}
                </div>
              );
              return sqSlug ? (
                <Link href={`/squadron/${sqSlug}`} title={`View all ${memorial.squadron} memorials`} style={{ textDecoration: "none" }}>
                  {badge}
                </Link>
              ) : badge;
            })()}
            <div style={{ flex: 1, display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "1rem" }}>
              {memorial.aircraft_type && <DetailItem label="Aircraft Type" value={memorial.aircraft_type} />}
              {memorial.serial_number && <DetailItem label="Serial Number" value={memorial.serial_number} />}
              {memorial.aircraft_code && <DetailItem label="Aircraft Code" value={memorial.aircraft_code} />}
              {memorial.squadron && (() => {
                const sqSlug = getSquadronSlugForName(memorial.squadron);
                return sqSlug ? (
                  <div>
                    <div style={{ fontSize: "0.7rem", color: "#8b7355", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.2rem" }}>Squadron</div>
                    <Link href={`/squadron/${sqSlug}`} style={{ color: "#7a4500", fontWeight: 500 }}>{memorial.squadron}</Link>
                  </div>
                ) : (
                  <DetailItem label="Squadron" value={memorial.squadron} />
                );
              })()}
              {memorial.station && <DetailItem label="Station" value={memorial.station} />}
              {memorial.crash_date && <DetailItem label="Date of Loss" value={memorial.crash_date} />}
              {memorial.operation_type && <DetailItem label="Operation Type" value={memorial.operation_type} />}
              {memorial.operation_target && <DetailItem label="Target" value={memorial.operation_target} />}
              {memorial.cause_of_loss && <DetailItem label="Cause of Loss" value={memorial.cause_of_loss} />}
            </div>
          </div>
        </section>
      )}

      {/* Crew Table */}
      {memorial.crew && memorial.crew.length > 0 && (() => {
        // Only show photos that are actual crew/personnel shots — not memorial plaques,
        // graves, or landscapes that happen to mention "crew" in the caption.
        const crewKeywords = ["crew", "aircrew", "airmen", "group photo", "team photo", "crew of", "crew member", "portrait"];
        const notCrewPhoto = ["memorial", "plaque", "names", "grave", "cemetery", "bench", "inscription", "stone", "cross", "site", "view", "distance", "setting", "detail"];
        const groupCrewPhotos = (memorial.photos || []).filter((p) => {
          const caption = (p.caption || "").toLowerCase();
          const hasCrew = crewKeywords.some((kw) => caption.includes(kw));
          const isMemorialShot = notCrewPhoto.some((kw) => caption.includes(kw));
          return hasCrew && !isMemorialShot;
        });
        return (
          <section style={{ marginBottom: "2.5rem" }} aria-label="Crew members">
            <h2 style={sectionHeading}>
              Crew ({memorial.crew.length} {memorial.crew.length === 1 ? "member" : "members"})
            </h2>
            {groupCrewPhotos.length > 0 && (
              <div style={{ marginBottom: "1.5rem" }}>
                {groupCrewPhotos.map((photo, i) => (
                  <figure key={i} style={{ margin: "0 0 1rem 0" }}>
                    <div style={{
                      borderRadius: 8,
                      overflow: "hidden",
                      border: "1px solid #e0dcd5",
                      borderLeft: "3px solid #8b7355",
                      position: "relative",
                      aspectRatio: "16/9",
                      maxHeight: 360,
                    }}>
                      <Image
                        src={`/images/memorials/${photo.filename}`}
                        alt={photo.caption || `${memorial.title} crew photograph`}
                        fill
                        style={{ objectFit: "contain" }}
                        sizes="(max-width: 900px) 100vw, 860px"
                        unoptimized
                      />
                    </div>
                    {photo.caption && (
                      <figcaption style={{ fontSize: "0.85rem", color: "#666", marginTop: "0.5rem", fontStyle: "italic" }}>
                        {photo.caption}
                        {photo.credit && <span style={{ color: "#999" }}> — Credit: {photo.credit}</span>}
                      </figcaption>
                    )}
                  </figure>
                ))}
              </div>
            )}
            <CrewTable crew={memorial.crew} />
          </section>
        );
      })()}

      {/* Crew Summary (when no detailed crew array) */}
      {memorial.crew_summary && (!memorial.crew || memorial.crew.length === 0) && (
        <section style={{ marginBottom: "2.5rem" }}>
          <h2 style={sectionHeading}>Crew</h2>
          <div style={cardBox}>
            {memorial.crew_summary}
          </div>
        </section>
      )}

      {/* Crew CTA (when no crew data at all) */}
      {(!memorial.crew || memorial.crew.length === 0) && !memorial.crew_summary && (
        <section style={{ marginBottom: "2.5rem" }}>
          <h2 style={sectionHeading}>Crew</h2>
          <div style={{
            ...cardBox,
            backgroundColor: "#f8f6f2",
            border: "1px dashed #c9b98a",
            textAlign: "center",
            padding: "2rem 1.5rem",
          }}>
            <p style={{ fontSize: "1rem", color: "#555", marginBottom: "0.75rem", lineHeight: 1.7 }}>
              We don&apos;t yet have crew details for this memorial. Do you know who served aboard this aircraft?
            </p>
            <p style={{ fontSize: "0.9rem", color: "#777", marginBottom: "1rem", lineHeight: 1.6 }}>
              Family connections, service records, or details from the memorial inscription would help us honour these crew members by name.
            </p>
            <a
              href={`mailto:admin@bombermemorial.co.uk?subject=Crew%20information%3A%20${encodeURIComponent(memorial.title)}&body=Memorial%3A%20${encodeURIComponent(memorial.title)}%0APage%3A%20https%3A%2F%2Fbombermemorial.co.uk%2Fmemorial%2F${memorial.id}%0A%0APlease%20share%20any%20crew%20details%20you%20have%3A%0A%0A`}
              style={{
                display: "inline-block",
                padding: "0.5rem 1.25rem",
                backgroundColor: "#1a2332",
                color: "#c9b98a",
                borderRadius: 6,
                textDecoration: "none",
                fontSize: "0.9rem",
                fontWeight: 600,
              }}
            >
              Share crew information
            </a>
          </div>
        </section>
      )}

      {/* Full Narrative Content — the scraped detailed records displayed directly */}
      {fullNarratives.length > 0 && (
        <section style={{ marginBottom: "2.5rem" }}>
          <h2 style={sectionHeading}>Detailed Record</h2>
          <p style={{ fontSize: "0.85rem", color: "#666", marginBottom: "1rem" }}>
            Compiled from heritage archives and aviation records. Source links provided below for original materials.
          </p>
          {fullNarratives.map((narrative, i) => {
            // Clean up the raw narrative: split on newlines, filter empty, render as paragraphs
            const lines = narrative.full_narrative!
              .replace(/&bull;/g, "")
              .replace(/\\n/g, "\n")
              .split("\n")
              .map(l => l.trim())
              .filter(l => l.length > 0)
              // Filter out boilerplate/navigation text
              .filter(l => !l.includes("Internet Explorer"))
              .filter(l => !l.includes("Searchable Lists"))
              .filter(l => !l.includes("Check our Research databases"))
              .filter(l => !l.includes("We seek additional information"))
              .filter(l => !l.includes("contact us via the Helpdesk"))
              .filter(l => !l.includes("Add to or correct this story"))
              .filter(l => !l.includes("Kracker Archive"))
              .filter(l => !l.includes("Archive Report: Allied Forces"));

            return (
              <div key={i} style={{
                backgroundColor: "#ffffff",
                border: "1px solid #e0dcd5",
                borderLeft: "3px solid #7a4500",
                borderRadius: "0 8px 8px 0",
                padding: "1.5rem 2rem",
                marginBottom: "1rem",
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                  <span style={{ fontSize: "0.8rem", color: "#7a4500", fontWeight: 600 }}>
                    Source: {narrative.source_site}
                  </span>
                  {narrative.date_retrieved && (
                    <span style={{ fontSize: "0.75rem", color: "#999" }}>
                      Retrieved {narrative.date_retrieved}
                    </span>
                  )}
                </div>
                <div style={{ lineHeight: 1.8, fontSize: "0.95rem", color: "#333" }}>
                  {lines.map((line, j) => {
                    // Detect crew member lines (contain service numbers like R/12345 or J/12345)
                    const isCrewLine = /^(Fl\/Eng|Nav|Air\/Bmr|W\/Op|Air\/Gnr|Pilot|P\/O|F\/O|Sgt|W\/O|F\/Sgt|F\/Lt|S\/Ldr):?\s/.test(line);
                    // Detect grave/burial lines
                    const isBurialLine = line.includes("Cemetery") && (line.includes("Sec") || line.includes("Grave") || line.includes("Row"));
                    // Detect inscription lines
                    const isInscription = line.includes("Grave inscription reads:");

                    if (isCrewLine) {
                      return (
                        <p key={j} style={{
                          margin: "0.3rem 0",
                          padding: "0.3rem 0.6rem",
                          backgroundColor: "#f8f6f2",
                          borderRadius: 4,
                          fontSize: "0.9rem",
                          fontFamily: "'Helvetica Neue', Arial, sans-serif",
                        }}>
                          {line}
                        </p>
                      );
                    }
                    if (isBurialLine) {
                      return (
                        <p key={j} style={{
                          margin: "0.5rem 0",
                          padding: "0.4rem 0.6rem",
                          borderLeft: "2px solid #8b7355",
                          fontSize: "0.9rem",
                          color: "#555",
                        }}>
                          {line}
                        </p>
                      );
                    }
                    if (isInscription) {
                      const parts = line.split("reads:");
                      return (
                        <p key={j} style={{ margin: "0.3rem 0 0.5rem 1rem", fontSize: "0.9rem" }}>
                          <span style={{ color: "#666" }}>Inscription: </span>
                          <em style={{ color: "#8b7355" }}>{parts[1]?.trim()}</em>
                        </p>
                      );
                    }
                    return <p key={j} style={{ margin: "0.4rem 0" }}>{line}</p>;
                  })}
                </div>
                <div style={{ marginTop: "1rem", borderTop: "1px solid #e0dcd5", paddingTop: "0.75rem" }}>
                  <a
                    href={narrative.original_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ fontSize: "0.8rem", color: "#7a4500" }}
                  >
                    View original at {narrative.source_site} &rarr;
                  </a>
                </div>
              </div>
            );
          })}
        </section>
      )}

      {/* Memorial Care */}
      {memorial.maintainer && (
        <section style={{ marginBottom: "2.5rem" }}>
          <h2 style={sectionHeading}>Memorial Care</h2>
          <div style={cardBox}>
            {memorial.maintainer.maintainer_type && (
              <div style={{ marginBottom: "1rem" }}>
                <span style={typeBadgeStyle}>
                  {memorial.maintainer.maintainer_type.replace(/-/g, " ")}
                </span>
              </div>
            )}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "1rem" }}>
              {memorial.maintainer.organisation && <DetailItem label="Organisation" value={memorial.maintainer.organisation} />}
              {memorial.maintainer.contact_email && (
                <div>
                  <div style={labelStyle}>Contact Email</div>
                  <div style={{ fontWeight: 500, color: "#333" }}>
                    <a href={`mailto:${memorial.maintainer.contact_email}`} style={{ color: "#7a4500" }}>
                      {memorial.maintainer.contact_email}
                    </a>
                  </div>
                </div>
              )}
              {memorial.maintainer.contact_phone && <DetailItem label="Contact Phone" value={memorial.maintainer.contact_phone} />}
              {memorial.maintainer.website && (
                <div>
                  <div style={labelStyle}>Website</div>
                  <div style={{ fontWeight: 500 }}>
                    <a href={memorial.maintainer.website} target="_blank" rel="noopener noreferrer" style={{ color: "#7a4500" }}>
                      {memorial.maintainer.website.replace(/^https?:\/\//, "").replace(/\/$/, "")}
                    </a>
                  </div>
                </div>
              )}
            </div>
            {memorial.maintainer.notes && (
              <p style={{ marginTop: "1rem", fontSize: "0.9rem", color: "#666", fontStyle: "italic", lineHeight: 1.6 }}>
                {memorial.maintainer.notes}
              </p>
            )}
          </div>
        </section>
      )}

      {/* Local Contacts */}
      {memorial.local_contacts && memorial.local_contacts.length > 0 && (
        <section style={{ marginBottom: "2.5rem" }}>
          <h2 style={sectionHeading}>Local Contacts</h2>
          <p style={{ fontSize: "0.9rem", color: "#666", marginBottom: "1rem" }}>
            These local organisations are connected to this memorial and may be able to help with information or visits.
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {memorial.local_contacts.map((contact, i) => (
              <div key={i} style={cardBox}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.5rem" }}>
                  <span style={{ fontWeight: 600, color: "#1a2332", fontSize: "1rem" }}>
                    {contact.org_name}
                  </span>
                  {contact.org_type && (
                    <span style={{
                      ...typeBadgeStyle,
                      backgroundColor: contact.org_type === "british_legion" ? "#1a2332" : "#eee8dd",
                      color: contact.org_type === "british_legion" ? "#d4c98c" : "#8b7355",
                    }}>
                      {contact.org_type.replace(/_/g, " ")}
                    </span>
                  )}
                </div>
                {contact.role && (
                  <p style={{ fontSize: "0.9rem", color: "#666", marginBottom: "0.5rem", fontStyle: "italic" }}>
                    {contact.role}
                  </p>
                )}
                <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem", fontSize: "0.9rem" }}>
                  {contact.contact_name && <span style={{ color: "#333" }}>{contact.contact_name}</span>}
                  {contact.contact_email && (
                    <a href={`mailto:${contact.contact_email}`} style={{ color: "#7a4500" }}>{contact.contact_email}</a>
                  )}
                  {contact.contact_phone && <span style={{ color: "#333" }}>{contact.contact_phone}</span>}
                  {contact.website && (
                    <a href={contact.website} target="_blank" rel="noopener noreferrer" style={{ color: "#7a4500" }}>
                      {contact.website.replace(/^https?:\/\//, "").replace(/\/$/, "")}
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* External Sources (summary links — for narratives without full content) */}
      {memorial.external_narratives && memorial.external_narratives.some(n => !n.full_narrative && n.summary) && (
        <section style={{ marginBottom: "2.5rem" }}>
          <h2 style={sectionHeading}>Further Reading</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {memorial.external_narratives.filter(n => !n.full_narrative && n.summary).map((narrative, i) => (
              <div key={i} style={{
                backgroundColor: "#ffffff",
                border: "1px solid #e0dcd5",
                borderLeft: "3px solid #7a4500",
                borderRadius: "0 8px 8px 0",
                padding: "1.25rem 1.5rem",
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                  {narrative.still_live === false ? (
                    <span style={{ color: "#555", fontWeight: 600 }}>
                      {narrative.source_site}
                    </span>
                  ) : (
                    <a href={narrative.original_url} target="_blank" rel="noopener noreferrer" style={{ color: "#7a4500", fontWeight: 600 }}>
                      {narrative.source_site}
                    </a>
                  )}
                  <span style={{ fontSize: "0.75rem", color: "#999" }}>
                    {narrative.date_retrieved && <>Retrieved {narrative.date_retrieved}</>}
                    {narrative.still_live === false && (
                      <span style={{ color: "#c44", marginLeft: narrative.date_retrieved ? "0.5rem" : undefined }}>(link may no longer be available)</span>
                    )}
                  </span>
                </div>
                {narrative.summary && <p style={{ fontSize: "0.95rem", color: "#333", lineHeight: 1.7, marginBottom: "0.5rem" }}>{narrative.summary}</p>}
                {narrative.link_description && (
                  <p style={{ fontSize: "0.85rem", color: "#555", lineHeight: 1.6, marginBottom: "0.5rem", fontStyle: "italic" }}>
                    What you&apos;ll find: {narrative.link_description}
                  </p>
                )}
                {narrative.key_details && <p style={{ fontSize: "0.9rem", color: "#666", fontStyle: "italic" }}>{narrative.key_details}</p>}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Related Memorials (same incident) */}
      {relatedMemorials.length > 0 && (
        <section style={{ marginBottom: "2.5rem" }}>
          <h2 style={sectionHeading}>Related Memorial{relatedMemorials.length > 1 ? 's' : ''}</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {relatedMemorials.map((related) => (
              <Link
                key={related.slug}
                href={`/memorial/${related.slug}`}
                style={{ textDecoration: "none", color: "inherit" }}
              >
                <div style={{
                  backgroundColor: "#f8f6f2",
                  borderLeft: "4px solid #7a4500",
                  borderRadius: "0 8px 8px 0",
                  padding: "1rem 1.25rem",
                  transition: "box-shadow 0.2s ease",
                  cursor: "pointer",
                }}>
                  <div style={{
                    fontFamily: "'Helvetica Neue', Arial, sans-serif",
                    color: "#1a2332",
                    fontSize: "0.95rem",
                    fontWeight: 600,
                    marginBottom: "0.25rem",
                  }}>
                    {related.title}
                  </div>
                  <div style={{ fontSize: "0.85rem", color: "#666", lineHeight: 1.5 }}>
                    {related.reason}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Nearby Memorials */}
      {nearbyMemorials.length > 0 && (
        <section style={{ marginBottom: "2.5rem" }}>
          <h2 style={sectionHeading}>Nearby Memorials</h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "1rem" }}>
            {nearbyMemorials.map((nearby) => (
              <Link
                key={nearby.id}
                href={`/memorial/${nearby.id}`}
                style={{ textDecoration: "none", color: "inherit" }}
              >
                <article style={{
                  backgroundColor: "#ffffff",
                  border: "1px solid #e0dcd5",
                  borderRadius: 8,
                  padding: "1rem 1.25rem",
                  transition: "box-shadow 0.2s ease, border-color 0.2s ease",
                  cursor: "pointer",
                  height: "100%",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.35rem",
                }} className="memorial-card">
                  <div style={{
                    fontFamily: "'Helvetica Neue', Arial, sans-serif",
                    color: "#1a2332",
                    fontSize: "0.95rem",
                    fontWeight: 600,
                    lineHeight: 1.3,
                  }}>
                    {nearby.title}
                  </div>
                  <div style={{ fontSize: "0.8rem", color: "#8b7355", fontWeight: 500 }}>
                    {nearby.distanceMiles.toFixed(1)} miles away
                  </div>
                  {nearby.county && (
                    <div style={{ fontSize: "0.8rem", color: "#666" }}>{nearby.county}</div>
                  )}
                </article>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Sources, Credits & Acknowledgements — unified section */}
      <section style={{ marginBottom: "2.5rem" }}>
        <h2 style={sectionHeading}>Sources</h2>
        <div style={{
          backgroundColor: "#1a2332",
          border: "1px solid #8b7355",
          borderRadius: 8,
          padding: "1.5rem 2rem",
          color: "#c9b98a",
        }}>
          {/* Heritage sources from external narratives */}
          {memorial.external_narratives && memorial.external_narratives.length > 0 && (
            <div style={{ marginBottom: "1rem" }}>
              {memorial.external_narratives.map((n, i) => (
                <div key={i} style={{ fontSize: "0.9rem", marginBottom: "0.25rem" }}>
                  {n.still_live === false ? (
                    <span style={{ color: "rgba(201,185,138,0.5)", textDecoration: "line-through" }}>
                      {n.source_site}
                    </span>
                  ) : (
                    <a href={n.original_url} target="_blank" rel="noopener noreferrer" style={{ color: "#c9b98a" }}>
                      {n.source_site}
                    </a>
                  )}
                  {n.still_live === false && (
                    <span style={{ color: "rgba(201,185,138,0.4)", fontSize: "0.8rem" }}> (link may no longer be available)</span>
                  )}
                  {n.date_retrieved && n.still_live !== false && <span style={{ color: "rgba(201,185,138,0.5)", fontSize: "0.8rem" }}> (retrieved {n.date_retrieved})</span>}
                </div>
              ))}
            </div>
          )}
          {/* Additional sources from sources array (deduplicated against external_narratives) */}
          {memorial.sources && memorial.sources.length > 0 && (() => {
            const narrativeSites = new Set((memorial.external_narratives || []).map(n => n.source_site?.toLowerCase()));
            const uniqueSources = memorial.sources.filter(s => !narrativeSites.has(s.title?.toLowerCase()));
            return uniqueSources.length > 0 ? (
              <div style={{ marginBottom: "1rem" }}>
                {uniqueSources.map((source, i) => (
                  <div key={i} style={{ fontSize: "0.9rem", marginBottom: "0.25rem" }}>
                    {source.url && source.still_live !== false ? (
                      <a href={source.url} target="_blank" rel="noopener noreferrer" style={{ color: "#c9b98a" }}>{source.title}</a>
                    ) : source.url && source.still_live === false ? (
                      <span style={{ color: "rgba(201,185,138,0.5)", textDecoration: "line-through" }}>{source.title}</span>
                    ) : (
                      <span>{source.title}</span>
                    )}
                    {source.still_live === false && (
                      <span style={{ color: "rgba(201,185,138,0.4)", fontSize: "0.8rem" }}> (link may no longer be available)</span>
                    )}
                    {source.type && source.still_live !== false && <span style={{ color: "rgba(201,185,138,0.5)", fontSize: "0.8rem" }}> ({source.type})</span>}
                  </div>
                ))}
              </div>
            ) : null;
          })()}
          {/* Credits */}
          <div style={{ borderTop: "1px solid rgba(139,115,85,0.3)", paddingTop: "0.75rem", marginTop: "0.5rem" }}>
            <div style={{ fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(201,185,138,0.6)", marginBottom: "0.3rem" }}>
              Credits &amp; Acknowledgements
            </div>
            {memorial.contributor && (
              <div style={{ marginBottom: "0.5rem" }}>
                <div style={{ fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(201,185,138,0.4)", marginBottom: "0.15rem" }}>
                  Record compiled by
                </div>
                <div style={{ fontSize: "1rem", fontWeight: 600 }}>{memorial.contributor}</div>
              </div>
            )}
            {memorial.additional_contributors && memorial.additional_contributors.length > 0 && (
              <div style={{ marginBottom: "0.5rem" }}>
                <div style={{ fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(201,185,138,0.4)", marginBottom: "0.15rem" }}>
                  With thanks to
                </div>
                {memorial.additional_contributors.map((c, i) => (
                  <div key={i} style={{ marginBottom: "0.4rem" }}>
                    <span style={{ fontWeight: 600, fontSize: "1rem" }}>{c.name}</span>
                    {c.role && <span style={{ fontSize: "0.9rem", color: "rgba(201,185,138,0.8)" }}> — {c.role}</span>}
                  </div>
                ))}
              </div>
            )}
          </div>
          {memorial.last_updated && (
            <div style={{ fontSize: "0.8rem", color: "rgba(201,185,138,0.5)", marginTop: "0.75rem", borderTop: "1px solid rgba(139,115,85,0.3)", paddingTop: "0.75rem" }}>
              Last updated {memorial.last_updated}
            </div>
          )}
        </div>
      </section>

      {/* Suggest a Correction */}
      <section style={{
        marginTop: "1rem",
        marginBottom: "2.5rem",
        padding: "1.25rem 1.5rem",
        backgroundColor: "#f8f6f2",
        border: "1px solid #e0dcd5",
        borderRadius: 8,
        textAlign: "center",
      }}>
        <p style={{ fontSize: "0.95rem", color: "#555", marginBottom: "0.75rem", lineHeight: 1.6 }}>
          Do you have additional information, photographs, or corrections for this record?
          We welcome contributions from researchers, families, and local communities.
        </p>
        <a
          href={`mailto:admin@bombermemorial.co.uk?subject=Correction%20or%20addition%3A%20${encodeURIComponent(memorial.title)}&body=Memorial%3A%20${encodeURIComponent(memorial.title)}%0APage%3A%20https%3A%2F%2Fbombermemorial.co.uk%2Fmemorial%2F${params.slug}%0A%0APlease%20describe%20the%20correction%20or%20addition%20below%3A%0A%0A`}
          style={{
            display: "inline-block",
            padding: "0.6rem 1.5rem",
            backgroundColor: "#1a2332",
            color: "#c9b98a",
            borderRadius: 6,
            fontSize: "0.9rem",
            fontFamily: "'Helvetica Neue', Arial, sans-serif",
            textDecoration: "none",
            letterSpacing: "0.03em",
          }}
        >
          Suggest a correction or addition
        </a>
      </section>

      {/* Stub CTA */}
      <StubCTA quality={memorial.data_quality || "Stub"} title={memorial.title} />
    </div>
  );
}

function DetailItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div style={labelStyle}>{label}</div>
      <div style={{ fontWeight: 500, color: "#333" }}>{value}</div>
    </div>
  );
}

const h1Style: React.CSSProperties = {
  fontFamily: "'Helvetica Neue', Arial, sans-serif",
  color: "#1a2332",
  fontSize: "2rem",
  marginBottom: "0.25rem",
  lineHeight: 1.2,
};

const sectionHeading: React.CSSProperties = {
  fontFamily: "'Helvetica Neue', Arial, sans-serif",
  color: "#1a2332",
  fontSize: "1.25rem",
  marginBottom: "1rem",
  paddingBottom: "0.5rem",
  borderBottom: "2px solid #e0dcd5",
};

const cardBox: React.CSSProperties = {
  backgroundColor: "#ffffff",
  border: "1px solid #e0dcd5",
  borderRadius: 8,
  padding: "1.5rem",
};

const narrativeBox: React.CSSProperties = {
  backgroundColor: "#ffffff",
  border: "1px solid #e0dcd5",
  borderLeft: "3px solid #8b7355",
  borderRadius: "0 8px 8px 0",
  padding: "1.5rem 2rem",
  lineHeight: 1.8,
  fontSize: "1rem",
};

const detailGrid: React.CSSProperties = {
  backgroundColor: "#ffffff",
  border: "1px solid #e0dcd5",
  borderRadius: 8,
  padding: "1.5rem",
  display: "flex",
  gap: "1.5rem",
  flexWrap: "wrap",
};

const labelStyle: React.CSSProperties = {
  fontSize: "0.7rem",
  color: "#999",
  textTransform: "uppercase",
  letterSpacing: "0.05em",
  fontFamily: "'Helvetica Neue', Arial, sans-serif",
  marginBottom: "0.2rem",
};

const typeBadgeStyle: React.CSSProperties = {
  fontSize: "0.7rem",
  padding: "0.2rem 0.6rem",
  borderRadius: 10,
  textTransform: "uppercase",
  letterSpacing: "0.05em",
  fontFamily: "'Helvetica Neue', Arial, sans-serif",
  backgroundColor: "#eee8dd",
  color: "#8b7355",
};

