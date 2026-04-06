"use client";

import { useEffect, useRef, useState } from "react";
import { Memorial } from "@/lib/types";

interface MemorialMapProps {
  memorials: Memorial[];
  center?: [number, number];
  zoom?: number;
  showFilter?: boolean;
}

// 4-tier confidence colours
const CONFIDENCE_COLOURS: Record<string, string> = {
  verified: "#22863a",    // Green
  confirmed: "#0969da",   // Blue
  approximate: "#d4a017", // Amber
  estimated: "#6e7781",   // Grey
};

const CONFIDENCE_LABELS: Record<string, string> = {
  verified: "Verified location",
  confirmed: "Confirmed location",
  approximate: "Approximate location",
  estimated: "Estimated location",
};

function createColourIcon(L: typeof import("leaflet"), colour: string) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 25 41" width="25" height="41">
    <path d="M12.5 0C5.6 0 0 5.6 0 12.5c0 8.5 12.5 28.5 12.5 28.5S25 21 25 12.5C25 5.6 19.4 0 12.5 0z" fill="${colour}" stroke="white" stroke-width="1.5"/>
    <circle cx="12.5" cy="12.5" r="5" fill="white" opacity="0.9"/>
  </svg>`;
  return L.divIcon({
    html: svg,
    className: "",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [0, -41],
  });
}

function posthogCapture(event: string, props: Record<string, unknown>) {
  if (typeof window !== "undefined" && (window as unknown as Record<string, unknown>).posthog) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (window as any).posthog.capture(event, props);
  }
}

export default function MemorialMap({
  memorials,
  center = [53.0, -1.0],
  zoom = 6,
  showFilter = false,
}: MemorialMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<unknown>(null);
  const markersRef = useRef<{ marker: unknown; status: string }[]>([]);
  const [filterVerifiedOnly, setFilterVerifiedOnly] = useState(false);

  const markersData = memorials.filter(
    (m) => m.latitude != null && m.longitude != null
  );

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    import("leaflet").then((L) => {
      if (!mapRef.current) return;

      const map = L.map(mapRef.current).setView(center, zoom);
      mapInstanceRef.current = map;

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      }).addTo(map);

      markersData.forEach((memorial) => {
        const status = memorial.location_confidence?.status || "estimated";
        const colour = CONFIDENCE_COLOURS[status] || CONFIDENCE_COLOURS.estimated;
        const icon = createColourIcon(L, colour);

        const marker = L.marker([memorial.latitude!, memorial.longitude!], { icon }).addTo(map);
        marker.bindPopup(
          `<div style="font-family: Georgia, serif;">` +
            `<strong><a href="/memorial/${memorial.id}" style="color: #2c5f8a;">${memorial.title}</a></strong>` +
            (memorial.location_name
              ? `<div style="font-size: 0.85rem; color: #666;">${memorial.location_name}</div>`
              : "") +
            `<div style="font-size: 0.75rem; color: ${colour}; margin-top: 0.25rem; font-weight: 600;">${CONFIDENCE_LABELS[status] || status}</div>` +
            `</div>`
        );

        marker.on("click", () => {
          posthogCapture("map_marker_click", {
            memorial_id: memorial.id,
            memorial_title: memorial.title,
            confidence_status: status,
          });
        });

        markersRef.current.push({ marker, status });
      });
    }).catch(() => {
      if (mapRef.current) {
        mapRef.current.innerHTML =
          '<div style="display:flex;align-items:center;justify-content:center;height:100%;font-family:Helvetica Neue,Arial,sans-serif;color:#8b7355;">Map could not be loaded. Please refresh the page.</div>';
      }
    });

    return () => {
      if (mapInstanceRef.current) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (mapInstanceRef.current as any).remove();
        mapInstanceRef.current = null;
        markersRef.current = [];
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Apply filter when toggle changes
  useEffect(() => {
    markersRef.current.forEach(({ marker, status }) => {
      const m = marker as { addTo: (map: unknown) => void; remove: () => void };
      if (filterVerifiedOnly) {
        if (status === "estimated" || status === "approximate") {
          m.remove();
        }
      } else {
        if (mapInstanceRef.current) {
          m.addTo(mapInstanceRef.current);
        }
      }
    });
  }, [filterVerifiedOnly]);

  function handleFilterToggle() {
    const next = !filterVerifiedOnly;
    setFilterVerifiedOnly(next);
    posthogCapture("map_filter_toggle", { filter_verified_only: next });
  }

  return (
    <div>
      {showFilter && (
        <div style={{ marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
          <button
            onClick={handleFilterToggle}
            style={{
              padding: "0.4rem 1rem",
              borderRadius: 6,
              border: `2px solid ${filterVerifiedOnly ? "#22863a" : "#e0dcd5"}`,
              backgroundColor: filterVerifiedOnly ? "#22863a" : "#ffffff",
              color: filterVerifiedOnly ? "#ffffff" : "#333",
              fontSize: "0.85rem",
              cursor: "pointer",
              fontFamily: "'Helvetica Neue', Arial, sans-serif",
              fontWeight: 500,
              transition: "all 0.2s ease",
            }}
          >
            {filterVerifiedOnly ? "✓ Verified/Confirmed only" : "Show verified/confirmed only"}
          </button>
          <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
            {Object.entries(CONFIDENCE_LABELS).map(([status, label]) => (
              <span key={status} style={{ display: "flex", alignItems: "center", gap: "0.3rem", fontSize: "0.75rem", color: "#555" }}>
                <span style={{ width: 10, height: 10, borderRadius: "50%", backgroundColor: CONFIDENCE_COLOURS[status], display: "inline-block" }} />
                {label.replace(" location", "")}
              </span>
            ))}
          </div>
        </div>
      )}
      <div
        ref={mapRef}
        style={{
          height: 450,
          width: "100%",
          borderRadius: 8,
          overflow: "hidden",
          border: "2px solid #8b7355",
          backgroundColor: "#e8e4de",
        }}
      />
    </div>
  );
}
