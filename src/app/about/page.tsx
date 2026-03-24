import { Metadata } from "next";
import { getMemorialStats } from "@/lib/data";
import Link from "next/link";

export const metadata: Metadata = {
  title: "About",
  description:
    "About the Bomber Command Memorial Register - honouring the memorials and aircrew of RAF Bomber Command.",
};

export default function AboutPage() {
  const stats = getMemorialStats();

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: "2rem 1.5rem" }}>
      {/* Breadcrumb */}
      <nav style={{ marginBottom: "1.5rem", fontSize: "0.85rem" }}>
        <Link href="/" style={{ color: "#2c5f8a" }}>
          Home
        </Link>
        <span style={{ color: "#999", margin: "0 0.5rem" }}>/</span>
        <span style={{ color: "#999" }}>About</span>
      </nav>

      <h1
        style={{
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
          color: "#1a2332",
          fontSize: "2rem",
          marginBottom: "2rem",
          lineHeight: 1.2,
        }}
      >
        About the Bomber Command
        <br />
        Memorial Register
      </h1>

      {/* Gold divider */}
      <div
        style={{
          width: 60,
          height: 2,
          backgroundColor: "#8b7355",
          marginBottom: "2rem",
        }}
      />

      <div style={{ lineHeight: 1.8, fontSize: "1.05rem" }}>
        <p style={{ marginBottom: "1.5rem" }}>
          The Bomber Command Memorial Register is a digital archive dedicated to
          recording and honouring the memorials, crash sites, and aircrew of RAF
          Bomber Command during the Second World War, 1939&ndash;1945.
        </p>

        <p style={{ marginBottom: "1.5rem" }}>
          Bomber Command suffered one of the highest casualty rates of any branch
          of service during the war. Of the 125,000 aircrew who served, 55,573
          were killed &mdash; a loss rate of 44.4%. Many were very young men,
          drawn from across the Commonwealth and Allied nations, who gave their
          lives in the skies over occupied Europe.
        </p>

        <p style={{ marginBottom: "1.5rem" }}>
          Across the United Kingdom and beyond, communities have erected
          memorials to remember the crews who fell near their homes. Some are
          grand stone monuments; others are simple plaques on a village wall.
          Each one tells a story of courage, sacrifice, and remembrance.
        </p>

        <h2
          style={{
            fontFamily: "'Helvetica Neue', Arial, sans-serif",
            color: "#1a2332",
            fontSize: "1.4rem",
            marginTop: "2.5rem",
            marginBottom: "1rem",
            paddingBottom: "0.5rem",
            borderBottom: "2px solid #e0dcd5",
          }}
        >
          Our Mission
        </h2>

        <p style={{ marginBottom: "1.5rem" }}>
          This register aims to document every known memorial to Bomber Command
          aircrew, wherever they may be found. For each memorial we record its
          location, the crew it commemorates, the aircraft involved, and the
          circumstances of the loss. We believe that every crew member deserves
          to be remembered by name.
        </p>

        <p style={{ marginBottom: "1.5rem" }}>
          The register currently contains{" "}
          <strong>{stats.totalMemorials} memorials</strong> across{" "}
          <strong>{stats.countries} countries</strong>. Many entries are partial
          &mdash; we know a memorial exists, but the full story remains to be
          told. We welcome contributions from researchers, local historians,
          families, and anyone with information to share.
        </p>

        <h2
          style={{
            fontFamily: "'Helvetica Neue', Arial, sans-serif",
            color: "#1a2332",
            fontSize: "1.4rem",
            marginTop: "2.5rem",
            marginBottom: "1rem",
            paddingBottom: "0.5rem",
            borderBottom: "2px solid #e0dcd5",
          }}
        >
          Contributors
        </h2>

        <p style={{ marginBottom: "1.5rem" }}>
          This project was founded by <strong>Keith Binley</strong>, who has
          spent years researching and photographing Bomber Command memorials
          across the United Kingdom. The international data has been contributed
          by <strong>Charlie Leitheiser</strong>, who has documented memorials
          across Europe, North America, and the Asia-Pacific.
        </p>

        <p style={{ marginBottom: "1.5rem" }}>
          We are grateful to the many local historians, parish councils,
          aviation archaeologists, and families who have shared their knowledge
          and photographs.
        </p>

        <h2
          style={{
            fontFamily: "'Helvetica Neue', Arial, sans-serif",
            color: "#1a2332",
            fontSize: "1.4rem",
            marginTop: "2.5rem",
            marginBottom: "1rem",
            paddingBottom: "0.5rem",
            borderBottom: "2px solid #e0dcd5",
          }}
        >
          How to Contribute
        </h2>

        <p style={{ marginBottom: "1.5rem" }}>
          If you know of a memorial not listed here, or can add photographs,
          crew details, narratives, or corrections to an existing entry, we
          would be delighted to hear from you. Many entries in the register are
          marked as &ldquo;Stub&rdquo; or &ldquo;Partial&rdquo; &mdash; meaning
          we know the memorial exists but lack the full details.
        </p>

        <p style={{ marginBottom: "1.5rem" }}>
          Please email us at{" "}
          <a href="mailto:admin@bombermemorial.co.uk" style={{ color: "#2c5f8a" }}>
            admin@bombermemorial.co.uk
          </a>{" "}
          with any information you can share. Every memorial page also has a
          &ldquo;Suggest a correction&rdquo; link at the bottom — we actively
          welcome corrections from local communities who know these sites best.
        </p>

        {/* Remembrance quote */}
        <blockquote
          style={{
            borderLeft: "3px solid #8b7355",
            margin: "2.5rem 0",
            padding: "1.25rem 1.75rem",
            backgroundColor: "#ffffff",
            fontStyle: "italic",
            fontSize: "1.1rem",
            color: "#555",
            borderRadius: "0 8px 8px 0",
          }}
        >
          &ldquo;They shall grow not old, as we that are left grow old:
          <br />
          Age shall not weary them, nor the years condemn.
          <br />
          At the going down of the sun and in the morning
          <br />
          We will remember them.&rdquo;
          <div
            style={{
              fontStyle: "normal",
              fontSize: "0.85rem",
              color: "#999",
              marginTop: "0.75rem",
            }}
          >
            &mdash; Laurence Binyon, &ldquo;For the Fallen&rdquo; (1914)
          </div>
        </blockquote>
      </div>
    </div>
  );
}
