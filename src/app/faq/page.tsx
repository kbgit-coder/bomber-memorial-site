import { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "FAQ",
  description: "Frequently asked questions about the Bomber Command Memorial Register.",
};

export default function FAQPage() {
  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: "2rem 1.5rem" }}>
      <nav style={{ marginBottom: "1.5rem", fontSize: "0.85rem" }}>
        <Link href="/" style={{ color: "#7a4500" }}>Home</Link>
        <span style={{ color: "#999", margin: "0 0.5rem" }}>/</span>
        <span style={{ color: "#999" }}>FAQ</span>
      </nav>

      <h1 style={{
        fontFamily: "'Helvetica Neue', Arial, sans-serif",
        color: "#1a2332",
        fontSize: "2rem",
        marginBottom: "1.5rem",
      }}>
        Frequently Asked Questions
      </h1>

      <p style={{ fontSize: "1rem", color: "#666", lineHeight: 1.8 }}>
        This page is coming soon. In the meantime, please{" "}
        <Link href="/contact" style={{ color: "#7a4500" }}>contact us</Link>{" "}
        with any questions.
      </p>
    </div>
  );
}
