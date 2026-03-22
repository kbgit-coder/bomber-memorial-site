"use client";

import { useEffect, useState } from "react";
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
  const [MapComponents, setMapComponents] = useState<{
    MapContainer: React.ComponentType<Record<string, unknown>>;
    TileLayer: React.ComponentType<Record<string, unknown>>;
    Marker: React.ComponentType<Record<string, unknown>>;
    Popup: React.ComponentType<Record<string, unknown>>;
  } | null>(null);

  useEffect(() => {
    import("react-leaflet").then((mod) => {
      setMapComponents({
        MapContainer: mod.MapContainer as unknown as React.ComponentType<Record<string, unknown>>,
        TileLayer: mod.TileLayer as unknown as React.ComponentType<Record<string, unknown>>,
        Marker: mod.Marker as unknown as React.ComponentType<Record<string, unknown>>,
        Popup: mod.Popup as unknown as React.ComponentType<Record<string, unknown>>,
      });
    });

    // Fix Leaflet default icon issue
    import("leaflet").then((L) => {
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
    });
  }, []);

  const markersData = memorials.filter(
    (m) => m.latitude != null && m.longitude != null
  );

  if (!MapComponents) {
    return (
      <div
        style={{
          height: 450,
          backgroundColor: "#e8e4de",
          borderRadius: 8,
          border: "2px solid #8b7355",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
          color: "#8b7355",
        }}
      >
        Loading map...
      </div>
    );
  }

  const { MapContainer, TileLayer, Marker, Popup } = MapComponents;

  return (
    <MapContainer center={center} zoom={zoom} scrollWheelZoom={false}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {markersData.map((memorial) => (
        <Marker
          key={memorial.id}
          position={[memorial.latitude!, memorial.longitude!]}
        >
          <Popup>
            <div style={{ fontFamily: "Georgia, serif" }}>
              <strong>
                <a
                  href={`/memorial/${memorial.id}`}
                  style={{ color: "#2c5f8a" }}
                >
                  {memorial.title}
                </a>
              </strong>
              {memorial.location_name && (
                <div style={{ fontSize: "0.85rem", color: "#666" }}>
                  {memorial.location_name}
                </div>
              )}
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
