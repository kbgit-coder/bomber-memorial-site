"use client";

import { useState } from "react";

interface HelpVerifyFormProps {
  memorialId: string;
  memorialTitle: string;
}

// Form handler running on Dell, accessible on Tailscale; for static export we POST directly
const FORM_HANDLER = "http://192.168.0.114:3458/submit-verify";

function posthogCapture(event: string, props: Record<string, unknown>) {
  if (typeof window !== "undefined" && (window as unknown as Record<string, unknown>).posthog) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (window as any).posthog.capture(event, props);
  }
}

export default function HelpVerifyForm({ memorialId, memorialTitle }: HelpVerifyFormProps) {
  const [open, setOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [source, setSource] = useState("");
  const [lat, setLat] = useState("");
  const [lng, setLng] = useState("");

  function handleOpen() {
    setOpen(true);
    posthogCapture("help_verify_cta_click", {
      memorial_id: memorialId,
      memorial_title: memorialTitle,
    });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    const payload = {
      memorial_id: memorialId,
      memorial_title: memorialTitle,
      name: name.trim(),
      email: email.trim(),
      source: source.trim(),
      corrected_lat: lat.trim() || null,
      corrected_lng: lng.trim() || null,
    };

    try {
      const res = await fetch(FORM_HANDLER, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        setSubmitted(true);
        posthogCapture("form_submission", {
          form_type: "help_verify",
          memorial_id: memorialId,
          has_coordinates: !!(lat && lng),
        });
      } else {
        // Fall back to mailto if form handler unavailable
        const subject = encodeURIComponent(`Location verification: ${memorialTitle}`);
        const body = encodeURIComponent(
          `Memorial: ${memorialTitle}\nID: ${memorialId}\n\nYour name: ${name}\nYour email: ${email}\n\nEvidence / source:\n${source}\n\nCorrected coordinates (if known):\nLat: ${lat}\nLng: ${lng}`
        );
        window.location.href = `mailto:admin@bombermemorial.co.uk?subject=${subject}&body=${body}`;
        setSubmitted(true);
        posthogCapture("form_submission", {
          form_type: "help_verify_mailto_fallback",
          memorial_id: memorialId,
        });
      }
    } catch {
      // Network error — use mailto fallback
      const subject = encodeURIComponent(`Location verification: ${memorialTitle}`);
      const body = encodeURIComponent(
        `Memorial: ${memorialTitle}\nID: ${memorialId}\n\nYour name: ${name}\nYour email: ${email}\n\nEvidence / source:\n${source}\n\nCorrected coordinates (if known):\nLat: ${lat}\nLng: ${lng}`
      );
      window.location.href = `mailto:admin@bombermemorial.co.uk?subject=${subject}&body=${body}`;
      setSubmitted(true);
      posthogCapture("form_submission", {
        form_type: "help_verify_mailto_fallback",
        memorial_id: memorialId,
      });
    } finally {
      setSubmitting(false);
    }
  }

  if (!open) {
    return (
      <div style={{
        padding: "1.25rem 1.5rem",
        backgroundColor: "#fff8e1",
        border: "1px solid #d4a017",
        borderLeft: "4px solid #d4a017",
        borderRadius: "0 8px 8px 0",
        marginBottom: "1.5rem",
      }}>
        <p style={{ fontSize: "0.9rem", color: "#5a4a1e", marginBottom: "0.75rem", lineHeight: 1.6 }}>
          <strong>Help us verify this location.</strong> This memorial&apos;s position is {
            memorialId ? "not yet precisely confirmed" : "approximate"
          }. If you have local knowledge, photographs, or documentary evidence of the exact site, we&apos;d love to hear from you.
        </p>
        <button
          onClick={handleOpen}
          style={{
            padding: "0.5rem 1.25rem",
            backgroundColor: "#d4a017",
            color: "#ffffff",
            border: "none",
            borderRadius: 6,
            fontSize: "0.875rem",
            fontFamily: "'Helvetica Neue', Arial, sans-serif",
            fontWeight: 600,
            cursor: "pointer",
            letterSpacing: "0.03em",
          }}
        >
          Help verify this location
        </button>
      </div>
    );
  }

  if (submitted) {
    return (
      <div style={{
        padding: "1.5rem",
        backgroundColor: "#dcfce7",
        border: "1px solid #22863a",
        borderRadius: 8,
        marginBottom: "1.5rem",
        textAlign: "center",
      }}>
        <p style={{ color: "#22863a", fontWeight: 600, marginBottom: "0.5rem" }}>Thank you for your contribution</p>
        <p style={{ color: "#166534", fontSize: "0.9rem" }}>
          Your information has been sent to the Bomber Memorial team. We review all submissions and will update the record if your evidence confirms the location.
        </p>
      </div>
    );
  }

  return (
    <div style={{
      padding: "1.5rem",
      backgroundColor: "#fff8e1",
      border: "1px solid #d4a017",
      borderLeft: "4px solid #d4a017",
      borderRadius: "0 8px 8px 0",
      marginBottom: "1.5rem",
    }}>
      <h3 style={{ fontFamily: "'Helvetica Neue', Arial, sans-serif", color: "#1a2332", fontSize: "1rem", marginBottom: "0.25rem" }}>
        Help verify this location
      </h3>
      <p style={{ fontSize: "0.85rem", color: "#666", marginBottom: "1.25rem" }}>
        Share your evidence or knowledge about the exact location of this memorial.
      </p>

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

        <div style={{ marginBottom: "0.75rem" }}>
          <label style={labelStyle}>Your source or evidence <span style={{ color: "#c44" }}>*</span></label>
          <textarea
            value={source}
            onChange={e => setSource(e.target.value)}
            required
            rows={3}
            placeholder="e.g. OS map reference, local history book, personal visit, family records..."
            style={{ ...inputStyle, resize: "vertical", minHeight: 72 }}
          />
        </div>

        <div style={{ marginBottom: "1rem" }}>
          <label style={labelStyle}>Corrected coordinates (optional)</label>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <input
              type="text"
              value={lat}
              onChange={e => setLat(e.target.value)}
              placeholder="Latitude, e.g. 53.1234"
              style={inputStyle}
              pattern="-?[0-9]{1,3}(\.[0-9]+)?"
            />
            <input
              type="text"
              value={lng}
              onChange={e => setLng(e.target.value)}
              placeholder="Longitude, e.g. -1.5678"
              style={inputStyle}
              pattern="-?[0-9]{1,3}(\.[0-9]+)?"
            />
          </div>
          <p style={{ fontSize: "0.75rem", color: "#999", marginTop: "0.3rem" }}>
            Decimal degrees format. Leave blank if unsure.
          </p>
        </div>

        {error && (
          <p style={{ color: "#c44", fontSize: "0.85rem", marginBottom: "0.75rem" }}>{error}</p>
        )}

        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
          <button
            type="submit"
            disabled={submitting}
            style={{
              padding: "0.5rem 1.25rem",
              backgroundColor: submitting ? "#999" : "#d4a017",
              color: "#ffffff",
              border: "none",
              borderRadius: 6,
              fontSize: "0.875rem",
              fontFamily: "'Helvetica Neue', Arial, sans-serif",
              fontWeight: 600,
              cursor: submitting ? "not-allowed" : "pointer",
            }}
          >
            {submitting ? "Sending..." : "Submit"}
          </button>
          <button
            type="button"
            onClick={() => setOpen(false)}
            style={{
              padding: "0.5rem 1rem",
              backgroundColor: "transparent",
              border: "1px solid #d4a017",
              borderRadius: 6,
              fontSize: "0.875rem",
              color: "#5a4a1e",
              cursor: "pointer",
            }}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
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
  border: "1px solid #d4a017",
  borderRadius: 6,
  fontSize: "0.9rem",
  fontFamily: "Georgia, serif",
  backgroundColor: "#fffbf0",
  boxSizing: "border-box",
  outline: "none",
  color: "#333",
};
