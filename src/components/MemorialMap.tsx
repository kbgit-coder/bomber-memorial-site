"use client";

import { useEffect, useRef } from "react";
import { Memorial } from "@/lib/types";

interface MemorialMapProps {
  memorials: Memorial[];
  center?: [number, number];
  zoom?: number;
}

export default function MemorialMap({
  memorials,
  center = [53.0, -1.0],
  zoom = 6,
}: MemorialMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<unknown>(null);

  const markersData = memorials.filter(
    (m) => m.latitude != null && m.longitude != null
  );

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    import("leaflet").then((L) => {
      if (!mapRef.current) return;

      // Fix default icon paths
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl:
          "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        iconUrl:
          "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        shadowUrl:
          "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      });

      const map = L.map(mapRef.current).setView(center, zoom);
      mapInstanceRef.current = map;

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      }).addTo(map);

      markersData.forEach((memorial) => {
        const marker = L.marker([memorial.latitude!, memorial.longitude!]).addTo(map);
        marker.bindPopup(
          `<div style="font-family: Georgia, serif;">` +
            `<strong><a href="/memorial/${memorial.id}" style="color: #2c5f8a;">${memorial.title}</a></strong>` +
            (memorial.location_name
              ? `<div style="font-size: 0.85rem; color: #666;">${memorial.location_name}</div>`
              : "") +
            `</div>`
        );
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
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
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
  );
}
