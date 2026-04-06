"use client";

import { useEffect, useRef } from "react";
import { LocationConfidence, LocationConfidenceStatus } from "@/lib/types";

const TIER_CONFIG: Record<LocationConfidenceStatus, {
  colour: string;
  bg: string;
  label: string;
  tooltip: string;
}> = {
  verified: {
    colour: "#22863a",
    bg: "#dcfce7",
    label: "Verified location",
    tooltip: "This location has been independently verified against primary sources (e.g. aerial survey, OS map, or CWGC record). The coordinates are as accurate as our records allow.",
  },
  confirmed: {
    colour: "#0969da",
    bg: "#dbeafe",
    label: "Confirmed location",
    tooltip: "This location has been confirmed from reliable secondary sources such as local records, memorial plaques, or heritage organisation databases.",
  },
  approximate: {
    colour: "#d4a017",
    bg: "#fef9c3",
    label: "Approximate location",
    tooltip: "This location is approximate. The pin is placed in the general area of the crash or memorial site, but has not been confirmed against primary sources. If you know the exact location, please help us verify it.",
  },
  estimated: {
    colour: "#6e7781",
    bg: "#f3f4f6",
    label: "Estimated location",
    tooltip: "This location is an estimate based on limited information such as a village name or general area. The pin may be several miles from the actual site. We welcome corrections.",
  },
};

interface ConfidenceBadgeProps {
  confidence: LocationConfidence;
  memorialId: string;
}

function posthogCapture(event: string, props: Record<string, unknown>) {
  if (typeof window !== "undefined" && (window as unknown as Record<string, unknown>).posthog) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (window as any).posthog.capture(event, props);
  }
}

export default function ConfidenceBadge({ confidence, memorialId }: ConfidenceBadgeProps) {
  const config = TIER_CONFIG[confidence.status] || TIER_CONFIG.estimated;
  const tooltipRef = useRef<HTMLSpanElement>(null);
  const hasTracked = useRef(false);

  useEffect(() => {
    const el = tooltipRef.current;
    if (!el) return;
    const handleEnter = () => {
      if (!hasTracked.current) {
        posthogCapture("confidence_badge_hover", {
          memorial_id: memorialId,
          confidence_status: confidence.status,
        });
        hasTracked.current = true;
      }
    };
    el.addEventListener("mouseenter", handleEnter);
    return () => el.removeEventListener("mouseenter", handleEnter);
  }, [confidence.status, memorialId]);

  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", position: "relative" }}>
      <span
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "0.4rem",
          padding: "0.3rem 0.75rem",
          borderRadius: 12,
          backgroundColor: config.bg,
          color: config.colour,
          fontSize: "0.8rem",
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
          fontWeight: 600,
          border: `1px solid ${config.colour}40`,
        }}
      >
        <span style={{ width: 8, height: 8, borderRadius: "50%", backgroundColor: config.colour, display: "inline-block", flexShrink: 0 }} />
        {config.label}
      </span>
      <span
        ref={tooltipRef}
        title={config.tooltip}
        style={{
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          width: 18,
          height: 18,
          borderRadius: "50%",
          backgroundColor: "#e0dcd5",
          color: "#666",
          fontSize: "0.7rem",
          fontWeight: 700,
          cursor: "help",
          flexShrink: 0,
        }}
      >
        ?
      </span>
    </div>
  );
}
