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
    <div data-pagefind-ignore style={{ maxWidth: 800, margin: "0 auto", padding: "2rem 1.5rem" }}>
      {/* Breadcrumb */}
      <nav style={{ marginBottom: "1.5rem", fontSize: "0.85rem" }}>
        <Link href="/" style={{ color: "#7a4500" }}>
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
          The Bomber Command Memorial Register records the memorials, crash
          sites, and aircrew of RAF Bomber Command during the Second World
          War, 1939&ndash;1945. But it is about more than locations and
          facts. It is about unearthing the local stories that inspired each
          memorial &mdash; the crash itself, the community that witnessed it,
          and the connection between village and crew that endures to this day.
        </p>

        <p style={{ marginBottom: "1.5rem" }}>
          Bomber Command suffered one of the highest casualty rates of any
          branch of service during the war. Of the 125,000 aircrew who served,
          55,573 were killed &mdash; a loss rate of 44.4%. Many were very young
          men, drawn from across the Commonwealth and Allied nations, who gave
          their lives in the skies over occupied Europe.
        </p>

        <p style={{ marginBottom: "1.5rem" }}>
          When Bomber Command&rsquo;s institutional commemoration arrived sixty
          years late, the work of remembrance had long since fallen to civic
          society: parishes, local historians, schoolchildren, and the families
          of the dead. Across the United Kingdom, communities erected memorials
          to remember the crews who fell near their homes. Some are grand stone
          monuments; others are simple plaques on a village wall. Each one
          carries a local story of courage, loss, and remembrance that deserves
          to be told.
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
          aircrew and, for each one, to unearth the human story behind it: the
          crew who were lost, the circumstances of the crash, and the local
          people who chose to remember. We believe that every crew member
          deserves to be remembered by name, and every community that built a
          memorial deserves to have that act of remembrance recorded.
        </p>

        <p style={{ marginBottom: "1.5rem" }}>
          The register currently contains{" "}
          <strong>{stats.totalMemorials} memorials</strong>. Many entries are
          partial &mdash; we know a memorial exists, but the full story remains
          to be told. We welcome contributions from researchers, local
          historians, families, and anyone with information to share.
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
          This project was founded by <strong>Keith Binley</strong>, inspired
          by the memorial to Halifax MZ519 near his home in Farnsfield,
          Nottinghamshire. Sitting with the farmer who had campaigned for its
          erection &mdash; a man who, as a boy in 1944, witnessed the crew
          laid out in a field after the crash &mdash; Keith realised that
          these local stories were in danger of being lost as the eyewitness
          generation passes. The connection between the seven young men of 578
          Squadron and the village that continues to remember and commemorate
          them became the inspiration for this register.
        </p>

        <p style={{ marginBottom: "1.5rem" }}>
          We are grateful to the many local historians, parish councils,
          squadron associations, aviation archaeologists, and families who
          have shared their knowledge and photographs. Every memorial in this
          register exists because someone in a community decided that these
          crews should not be forgotten.
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
          <a href="mailto:admin@bombermemorial.co.uk" style={{ color: "#7a4500" }}>
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
