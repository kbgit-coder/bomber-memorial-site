"use client";

import { useEffect, useState, Component, ReactNode } from "react";
import { Memorial } from "@/lib/types";

// Error boundary to prevent map crashes from taking down the whole page
class MapErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  render() {
    if (this.state.hasError) {
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
          Map could not be loaded. Please refresh the page.
        </div>
      );
    }
    return this.props.children;
  }
}

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
  return (
    <MapErrorBoundary>
      <MemorialMapInner memorials={memorials} center={center} zoom={zoom} />
    </MapErrorBoundary>
  );
}

function MemorialMapInner({
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
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    Promise.all([import("react-leaflet"), import("leaflet")])
      .then(([mod, L]) => {
        // Fix Leaflet default icon issue
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

        setMapComponents({
          MapContainer: mod.MapContainer as unknown as React.ComponentType<Record<string, unknown>>,
          TileLayer: mod.TileLayer as unknown as React.ComponentType<Record<string, unknown>>,
          Marker: mod.Marker as unknown as React.ComponentType<Record<string, unknown>>,
          Popup: mod.Popup as unknown as React.ComponentType<Record<string, unknown>>,
        });
      })
      .catch(() => {
        setLoadError(true);
      });
  }, []);

  const markersData = memorials.filter(
    (m) => m.latitude != null && m.longitude != null
  );

  if (loadError) {
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
        Map could not be loaded. Please refresh the page.
      </div>
    );
  }

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
    <div style={{ height: 450, width: "100%", borderRadius: 8, overflow: "hidden", border: "2px solid #8b7355" }}>
      <MapContainer center={center} zoom={zoom} scrollWheelZoom={false} style={{ height: "100%", width: "100%" }}>
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
    </div>
  );
}
