import { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Site Terms",
  description: "Terms of use and cookies policy for the Bomber Command Memorial Register.",
};

export default function TermsPage() {
  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: "2rem 1.5rem" }}>
      <nav style={{ marginBottom: "1.5rem", fontSize: "0.85rem" }}>
        <Link href="/" style={{ color: "#2c5f8a" }}>Home</Link>
        <span style={{ color: "#999", margin: "0 0.5rem" }}>/</span>
        <span style={{ color: "#999" }}>Site Terms</span>
      </nav>

      <h1 style={{
        fontFamily: "'Helvetica Neue', Arial, sans-serif",
        color: "#1a2332",
        fontSize: "2rem",
        marginBottom: "1.5rem",
      }}>
        Site Terms &amp; Cookies Policy
      </h1>

      <div style={{ fontSize: "0.95rem", color: "#444", lineHeight: 1.8 }}>
        <h2 style={{ fontFamily: "'Helvetica Neue', Arial, sans-serif", color: "#1a2332", fontSize: "1.25rem", marginTop: "2rem" }}>
          Terms of Use
        </h2>
        <p>
          The Bomber Command Memorial Register is a free, community-driven resource dedicated to
          preserving the memory of RAF Bomber Command aircrew and their memorials. Content on this
          site is provided in good faith for educational and remembrance purposes.
        </p>
        <p>
          You are welcome to reference, share, and link to any page on this site. If you wish to
          reproduce substantial portions of our content, please{" "}
          <Link href="/contact" style={{ color: "#2c5f8a" }}>contact us</Link> first.
        </p>
        <p>
          While we strive for accuracy, historical records can be incomplete or contain errors. If
          you spot an inaccuracy, please let us know and we will correct it promptly.
        </p>

        <h2 style={{ fontFamily: "'Helvetica Neue', Arial, sans-serif", color: "#1a2332", fontSize: "1.25rem", marginTop: "2rem" }}>
          Cookies Policy
        </h2>
        <p>
          This site uses a small number of cookies to help us understand how visitors use the
          register so we can improve it over time.
        </p>
        <ul style={{ paddingLeft: "1.5rem" }}>
          <li style={{ marginBottom: "0.5rem" }}>
            <strong>Analytics (PostHog)</strong> &mdash; We use PostHog to collect anonymous usage
            data such as page views and navigation patterns. This helps us understand which memorials
            receive the most interest and where to focus our research efforts. No personally
            identifiable information is collected unless you choose to identify yourself.
          </li>
        </ul>
        <p>
          We do not use advertising cookies, social media tracking pixels, or any third-party
          marketing tools. Your visit here is about remembrance, not commerce.
        </p>

        <h2 style={{ fontFamily: "'Helvetica Neue', Arial, sans-serif", color: "#1a2332", fontSize: "1.25rem", marginTop: "2rem" }}>
          Data &amp; Privacy
        </h2>
        <p>
          Crew information published on this site is drawn from public historical records, official
          war diaries, Commonwealth War Graves Commission data, and community contributions. If you
          are a family member and have concerns about any information displayed, please{" "}
          <Link href="/contact" style={{ color: "#2c5f8a" }}>contact us</Link> and we will address
          your request promptly.
        </p>
      </div>
    </div>
  );
}
