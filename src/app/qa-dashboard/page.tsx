import { Metadata } from "next";
import { getQualityDashboardData } from "@/lib/data";
import QualityDashboard from "@/components/QualityDashboard";

export const metadata: Metadata = {
  title: "Quality Dashboard",
  robots: { index: false, follow: false },
};

export default function QADashboardPage() {
  const data = getQualityDashboardData();

  return (
    <div data-pagefind-ignore style={{ maxWidth: 1400, margin: "0 auto", padding: "2rem 1.5rem" }}>
      <div style={{ marginBottom: "2rem" }}>
        <h1 style={{
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
          color: "#1a2332",
          fontSize: "2rem",
          marginBottom: "0.5rem",
        }}>
          Quality Dashboard
        </h1>
        <p style={{ color: "#666", fontSize: "0.9rem" }}>
          SET NEW STANDARDS — per-page and per-section quality scoring.
          Bottom 5% flagged for review. Updated every build.
        </p>
      </div>
      <QualityDashboard data={data} />
    </div>
  );
}
