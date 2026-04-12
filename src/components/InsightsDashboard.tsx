"use client";

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, AreaChart, Area, LabelList,
} from "recharts";

interface InsightsData {
  totalMemorials: number;
  totalCrew: number;
  meanAge: number;
  killedCount: number;
  survivedCount: number;
  crewWithAge: number;
  crashesByYear: { year: string; count: number }[];
  crashCategories: { category: string; count: number }[];
  aircraftTypes: { aircraft: string; count: number }[];
  nationalities: { nationality: string; count: number }[];
  ageDistribution: { range: string; count: number }[];
  dataQuality: { quality: string; count: number }[];
}

// Site palette
const NAVY = "#1a2332";
const GOLD = "#c9b98a";
const WARM_BROWN = "#8b7355";
const CHART_COLOURS = [
  "#2c5f8a", "#c9b98a", "#8b7355", "#4a7c59", "#a85d3f",
  "#6b5b8a", "#3a7d7b", "#c4784a", "#5c7a3a", "#8a5c6b",
];
const PIE_COLOURS = ["#2c5f8a", "#c9b98a", "#8b7355", "#4a7c59", "#a85d3f", "#6b5b8a", "#3a7d7b", "#c4784a"];

function StatCard({ value, label, accent }: { value: string | number; label: string; accent?: string }) {
  return (
    <div style={{
      background: `linear-gradient(135deg, ${NAVY} 0%, #243447 100%)`,
      borderRadius: 12,
      padding: "1.5rem",
      flex: "1 1 200px",
      minWidth: 180,
      position: "relative",
      overflow: "hidden",
    }}>
      <div style={{
        position: "absolute",
        top: -20,
        right: -20,
        width: 80,
        height: 80,
        borderRadius: "50%",
        background: accent || GOLD,
        opacity: 0.08,
      }} />
      <div style={{
        fontSize: "2.25rem",
        fontWeight: 700,
        color: accent || GOLD,
        fontFamily: "'Helvetica Neue', Arial, sans-serif",
        lineHeight: 1.1,
        marginBottom: "0.4rem",
      }}>
        {typeof value === "number" ? value.toLocaleString() : value}
      </div>
      <div style={{
        fontSize: "0.8rem",
        color: "rgba(255,255,255,0.6)",
        textTransform: "uppercase",
        letterSpacing: "0.08em",
        fontFamily: "'Helvetica Neue', Arial, sans-serif",
        fontWeight: 500,
      }}>
        {label}
      </div>
    </div>
  );
}

function ChartCard({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <div style={{
      background: "#fff",
      borderRadius: 12,
      border: "1px solid #e8e4de",
      padding: "1.5rem",
      boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
    }}>
      <h3 style={{
        fontFamily: "'Helvetica Neue', Arial, sans-serif",
        fontSize: "1rem",
        fontWeight: 600,
        color: NAVY,
        marginBottom: subtitle ? "0.25rem" : "1.25rem",
        marginTop: 0,
      }}>
        {title}
      </h3>
      {subtitle && (
        <p style={{ fontSize: "0.8rem", color: "#888", marginTop: 0, marginBottom: "1.25rem" }}>
          {subtitle}
        </p>
      )}
      {children}
    </div>
  );
}

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: { value: number; name?: string }[]; label?: string }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: NAVY,
      color: "#fff",
      padding: "0.5rem 0.75rem",
      borderRadius: 6,
      fontSize: "0.8rem",
      fontFamily: "'Helvetica Neue', Arial, sans-serif",
      boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
    }}>
      <div style={{ fontWeight: 600, marginBottom: 2 }}>{label}</div>
      <div style={{ color: GOLD }}>{payload[0].value.toLocaleString()} {payload[0].value === 1 ? "memorial" : "memorials"}</div>
    </div>
  );
};

export default function InsightsDashboard({ data }: { data: InsightsData }) {
  const trainingPct = data.crashCategories.find(c => c.category === "Training");
  const trainingPercent = trainingPct
    ? Math.round((trainingPct.count / data.totalMemorials) * 100)
    : 0;

  // Peak year
  const peakYear = data.crashesByYear.reduce((a, b) => (b.count > a.count ? b : a), data.crashesByYear[0]);

  return (
    <div>
      {/* Hero stats row */}
      <div style={{
        display: "flex",
        gap: "1rem",
        flexWrap: "wrap",
        marginBottom: "2rem",
      }}>
        <StatCard value={data.totalMemorials} label="Memorials Recorded" />
        <StatCard value={data.totalCrew.toLocaleString()} label="Crew Members" accent="#e8c87a" />
        <StatCard value={data.meanAge} label="Average Age" accent="#7ecb7e" />
        <StatCard value={`${trainingPercent}%`} label="Training Accidents" accent="#e8907a" />
      </div>

      {/* Callout strip */}
      <div style={{
        background: "linear-gradient(90deg, #f8f6f2 0%, #fff 100%)",
        borderLeft: `4px solid ${WARM_BROWN}`,
        borderRadius: "0 8px 8px 0",
        padding: "1rem 1.5rem",
        marginBottom: "2rem",
        display: "flex",
        flexWrap: "wrap",
        gap: "2rem",
        alignItems: "center",
        fontSize: "0.9rem",
        color: "#555",
      }}>
        <span><strong style={{ color: NAVY }}>{peakYear?.year}</strong> was the deadliest year with <strong style={{ color: NAVY }}>{peakYear?.count}</strong> recorded incidents</span>
        <span><strong style={{ color: NAVY }}>{data.crewWithAge}</strong> crew members have age records &mdash; the youngest just <strong style={{ color: NAVY }}>18</strong></span>
        <span><strong style={{ color: NAVY }}>{data.nationalities.length}+</strong> nationalities served in Bomber Command</span>
      </div>

      {/* Charts grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 480px), 1fr))",
        gap: "1.5rem",
        marginBottom: "2rem",
      }}>
        {/* Crashes by year — area chart */}
        <ChartCard title="Incidents by Year" subtitle="Recorded crash and loss events across the war years">
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={data.crashesByYear} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
              <defs>
                <linearGradient id="yearGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2c5f8a" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#2c5f8a" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
              <XAxis dataKey="year" tick={{ fontSize: 12, fill: "#888" }} />
              <YAxis tick={{ fontSize: 12, fill: "#888" }} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="count" stroke="#2c5f8a" strokeWidth={2.5} fill="url(#yearGrad)">
                <LabelList dataKey="count" position="top" style={{ fontSize: 11, fontWeight: 600, fill: "#2c5f8a" }} />
              </Area>
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Crash categories — horizontal bar */}
        <ChartCard title="Cause of Loss" subtitle="Classification of recorded incidents">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.crashCategories} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eee" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 12, fill: "#888" }} />
              <YAxis type="category" dataKey="category" tick={{ fontSize: 11, fill: "#555" }} width={140} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                <LabelList dataKey="count" position="insideRight" style={{ fontSize: 11, fontWeight: 600, fill: "#fff" }} />
                {data.crashCategories.map((_, i) => (
                  <Cell key={i} fill={CHART_COLOURS[i % CHART_COLOURS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Nationalities — horizontal bar */}
        <ChartCard title="Crew Nationalities" subtitle="Top 10 nationalities among recorded crew members">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.nationalities} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eee" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 12, fill: "#888" }} />
              <YAxis type="category" dataKey="nationality" tick={{ fontSize: 11, fill: "#555" }} width={110} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                <LabelList dataKey="count" position="insideRight" style={{ fontSize: 11, fontWeight: 600, fill: "#fff" }} />
                {data.nationalities.map((_, i) => (
                  <Cell key={i} fill={CHART_COLOURS[i % CHART_COLOURS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Age distribution — bar chart */}
        <ChartCard title="Crew Age Distribution" subtitle={`Based on ${data.crewWithAge} crew members with recorded ages`}>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.ageDistribution} margin={{ top: 20, right: 20, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
              <XAxis dataKey="range" tick={{ fontSize: 12, fill: "#888" }} />
              <YAxis tick={{ fontSize: 12, fill: "#888" }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" radius={[4, 4, 0, 0]} fill="#4a7c59">
                <LabelList dataKey="count" position="top" style={{ fontSize: 11, fontWeight: 600, fill: "#4a7c59" }} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Aircraft types — bar chart */}
        <ChartCard title="Aircraft Types" subtitle="Most common aircraft in recorded incidents">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.aircraftTypes} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eee" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 12, fill: "#888" }} />
              <YAxis type="category" dataKey="aircraft" tick={{ fontSize: 11, fill: "#555" }} width={120} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                <LabelList dataKey="count" position="insideRight" style={{ fontSize: 11, fontWeight: 600, fill: "#fff" }} />
                {data.aircraftTypes.map((_, i) => (
                  <Cell key={i} fill={CHART_COLOURS[i % CHART_COLOURS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Data quality — pie */}
        <ChartCard title="Data Completeness" subtitle="How much of each memorial record is filled in">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "2rem", flexWrap: "wrap" }}>
            <ResponsiveContainer width={200} height={200}>
              <PieChart>
                <Pie
                  data={data.dataQuality}
                  dataKey="count"
                  nameKey="quality"
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={3}
                  strokeWidth={0}
                >
                  {data.dataQuality.map((_, i) => (
                    <Cell key={i} fill={PIE_COLOURS[i % PIE_COLOURS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {data.dataQuality.map((d, i) => (
                <div key={d.quality} style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.85rem" }}>
                  <div style={{
                    width: 12, height: 12, borderRadius: 3,
                    backgroundColor: PIE_COLOURS[i % PIE_COLOURS.length],
                  }} />
                  <span style={{ color: "#555" }}>
                    <strong style={{ color: NAVY }}>{d.count}</strong> {d.quality}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </ChartCard>
      </div>

      {/* Footer note */}
      <div style={{
        textAlign: "center",
        padding: "1.5rem",
        color: "#999",
        fontSize: "0.8rem",
        fontFamily: "'Helvetica Neue', Arial, sans-serif",
      }}>
        Data computed from {data.totalMemorials} memorial records. Figures update with each site build as new data is added.
      </div>
    </div>
  );
}
