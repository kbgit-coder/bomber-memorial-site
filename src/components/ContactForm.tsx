"use client";

import { useState } from "react";

export default function ContactForm() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const res = await fetch("/api/submit.php", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          type: "contact",
          site: "bombermemorial",
          name: name.trim(),
          email: email.trim(),
          message: message.trim(),
        }),
      });
      if (!res.ok) throw new Error("Submit failed");
      setSubmitted(true);
    } catch {
      setError("Unable to send your message. Please email us directly at admin@bombermemorial.co.uk");
    } finally {
      setSubmitting(false);
    }
  }

  if (submitted) {
    return (
      <div style={{
        padding: "1.5rem",
        backgroundColor: "#dcfce7",
        border: "1px solid #22863a",
        borderRadius: 8,
        textAlign: "center",
      }}>
        <p style={{ color: "#22863a", fontWeight: 600, marginBottom: "0.5rem" }}>Message sent</p>
        <p style={{ color: "#166534", fontSize: "0.9rem" }}>
          Thank you for getting in touch. We will respond as soon as we can.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginBottom: "0.75rem" }}>
        <div>
          <label style={labelStyle}>Your name</label>
          <input
            type="text"
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="e.g. John Smith"
            style={inputStyle}
          />
        </div>
        <div>
          <label style={labelStyle}>Your email <span style={{ color: "#c44" }}>*</span></label>
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
            placeholder="e.g. j.smith@example.com"
            style={inputStyle}
          />
        </div>
      </div>

      <div style={{ marginBottom: "1rem" }}>
        <label style={labelStyle}>Your message <span style={{ color: "#c44" }}>*</span></label>
        <textarea
          value={message}
          onChange={e => setMessage(e.target.value)}
          required
          rows={5}
          placeholder="Tell us about a memorial, share photographs, crew details, corrections, or anything else..."
          style={{ ...inputStyle, resize: "vertical", minHeight: 100 }}
        />
      </div>

      {error && (
        <p style={{ color: "#c44", fontSize: "0.85rem", marginBottom: "0.75rem" }}>{error}</p>
      )}

      <button
        type="submit"
        disabled={submitting}
        style={{
          padding: "0.6rem 1.5rem",
          backgroundColor: submitting ? "#999" : "#1a2332",
          color: "#c9b98a",
          border: "none",
          borderRadius: 6,
          fontSize: "0.9rem",
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
          fontWeight: 600,
          cursor: submitting ? "not-allowed" : "pointer",
          letterSpacing: "0.03em",
        }}
      >
        {submitting ? "Sending..." : "Send Message"}
      </button>
    </form>
  );
}

const labelStyle: React.CSSProperties = {
  display: "block",
  fontSize: "0.75rem",
  color: "#666",
  textTransform: "uppercase",
  letterSpacing: "0.05em",
  marginBottom: "0.3rem",
  fontFamily: "'Helvetica Neue', Arial, sans-serif",
};

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "0.5rem 0.75rem",
  border: "1px solid #d0ccc4",
  borderRadius: 6,
  fontSize: "0.9rem",
  fontFamily: "Georgia, serif",
  backgroundColor: "#faf9f6",
  boxSizing: "border-box",
  outline: "none",
  color: "#333",
};
