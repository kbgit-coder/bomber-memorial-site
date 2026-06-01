import { Metadata } from "next";
import { getInsightsData } from "@/lib/data";
import InsightsDashboard from "@/components/InsightsDashboard";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Insights",
  description:
    "Data insights from the Bomber Command Memorial Register — crew demographics, crash analysis, and memorial coverage.",
};

export default function InsightsPage() {
  const data = getInsightsData();

  return (
    <div data-pagefind-ignore style={{ maxWidth: 1200, margin: "0 auto", padding: "2rem 1.5rem" }}>
      {/* Breadcrumb */}
      <nav style={{ marginBottom: "1.5rem", fontSize: "0.85rem" }}>
        <Link href="/" style={{ color: "#7a4500" }}>
          Home
        </Link>
        <span style={{ color: "#999", margin: "0 0.5rem" }}>/</span>
        <span style={{ color: "#999" }}>Insights</span>
      </nav>

      <div style={{ marginBottom: "2.5rem" }}>
        <h1
          style={{
            fontFamily: "'Helvetica Neue', Arial, sans-serif",
            color: "#1a2332",
            fontSize: "2rem",
            marginBottom: "0.5rem",
            lineHeight: 1.2,
          }}
        >
          Register Insights
        </h1>
        <p style={{ color: "#666", fontSize: "1rem", lineHeight: 1.6, maxWidth: 700 }}>
          A living snapshot of the data behind the Bomber Command Memorial Register.
          These figures update automatically as new memorials and crew records are added.
        </p>
      </div>

      <InsightsDashboard data={data} />
    </div>
  );
}
