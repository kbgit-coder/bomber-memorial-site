import { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Contact",
  description: "Get in touch with the Bomber Command Memorial Register.",
};

export default function ContactPage() {
  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: "2rem 1.5rem" }}>
      <nav style={{ marginBottom: "1.5rem", fontSize: "0.85rem" }}>
        <Link href="/" style={{ color: "#2c5f8a" }}>Home</Link>
        <span style={{ color: "#999", margin: "0 0.5rem" }}>/</span>
        <span style={{ color: "#999" }}>Contact</span>
      </nav>

      <h1 style={{
        fontFamily: "'Helvetica Neue', Arial, sans-serif",
        color: "#1a2332",
        fontSize: "2rem",
        marginBottom: "1.5rem",
      }}>
        Contact Us
      </h1>

      <div style={{
        backgroundColor: "#f8f6f2",
        borderLeft: "4px solid #8b7355",
        borderRadius: "0 8px 8px 0",
        padding: "1.5rem",
        marginBottom: "2rem",
      }}>
        <p style={{ fontSize: "1rem", color: "#444", lineHeight: 1.8, marginBottom: "1rem" }}>
          We welcome contributions from researchers, families, local historians, and enthusiasts.
          Whether you have photographs, crew details, corrections, or know of a memorial not yet
          listed, we would love to hear from you.
        </p>
        <p style={{ fontSize: "1rem", color: "#444", lineHeight: 1.8, marginBottom: 0 }}>
          Please email us at{" "}
          <a
            href="mailto:admin@bombermemorial.co.uk"
            style={{ color: "#2c5f8a", fontWeight: 600 }}
          >
            admin@bombermemorial.co.uk
          </a>
        </p>
      </div>
    </div>
  );
}
