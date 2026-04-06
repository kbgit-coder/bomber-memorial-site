import { Metadata } from "next";
import { getAllMemorials } from "@/lib/data";
import MemorialMap from "@/components/MemorialMap";

export const metadata: Metadata = {
  title: "Memorial Map | Bomber Command Memorial Register",
  description:
    "Interactive map of all 208 Bomber Command memorials. Filter by location confidence: verified, confirmed, approximate, or estimated sites.",
};

export default function MapPage() {
  const allMemorials = getAllMemorials();

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "2rem 1.5rem" }}>
      <h1
        style={{
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
          color: "#1a2332",
          fontSize: "2rem",
          marginBottom: "0.5rem",
        }}
      >
        Memorial Map
      </h1>
      <p style={{ color: "#666", marginBottom: "1.5rem", lineHeight: 1.6 }}>
        All {allMemorials.length} memorials in the register. Use the filter to
        show only sites with confirmed or verified locations. Marker colours
        indicate location confidence.
      </p>
      <MemorialMap
        memorials={allMemorials}
        center={[53.0, -1.5]}
        zoom={6}
        showFilter={true}
      />
    </div>
  );
}
