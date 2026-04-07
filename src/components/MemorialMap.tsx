"use client";

import { useEffect, useRef } from "react";
import { Memorial } from "@/lib/types";
import "maplibre-gl/dist/maplibre-gl.css";

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
  const mapInstanceRef = useRef<maplibregl.Map | null>(null);

  const markersData = memorials.filter(
    (m) => m.latitude != null && m.longitude != null
  );

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    import("maplibre-gl").then((maplibregl) => {
      if (!mapRef.current) return;

      const map = new maplibregl.Map({
        container: mapRef.current,
        style: "https://tiles.openfreemap.org/styles/liberty",
        center: [center[1], center[0]], // MapLibre uses [lng, lat] not [lat, lng]
        zoom: zoom,
      });

      mapInstanceRef.current = map;

      map.addControl(new maplibregl.NavigationControl(), "top-right");

      map.on("load", () => {
        markersData.forEach((memorial) => {
          const popup = new maplibregl.Popup({ offset: 25 }).setHTML(
            `<div style="font-family: Georgia, serif;">` +
              `<strong><a href="/memorial/${memorial.id}" style="color: #2c5f8a;">${memorial.title}</a></strong>` +
              (memorial.location_name
                ? `<div style="font-size: 0.85rem; color: #666;">${memorial.location_name}</div>`
                : "") +
              `</div>`
          );

          new maplibregl.Marker({ color: "#2c5f8a" })
            .setLngLat([memorial.longitude!, memorial.latitude!])
            .setPopup(popup)
            .addTo(map);
        });
      });
    }).catch(() => {
      if (mapRef.current) {
        mapRef.current.innerHTML =
          '<div style="display:flex;align-items:center;justify-content:center;height:100%;font-family:Helvetica Neue,Arial,sans-serif;color:#8b7355;">Map could not be loaded. Please refresh the page.</div>';
      }
    });

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
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
