import { useDashboard } from "../../context/DashboardContext";
import { StatCard } from "./StatCard";

export function StatsRow() {
  const { stats } = useDashboard();

  const total = stats?.total_conversations ?? "-";
  const avgLatency =
    stats?.avg_latency && stats.avg_latency.total_ms > 0
      ? Math.round(stats.avg_latency.total_ms)
      : "-";
  const todayCount = stats?.avg_latency?.conversation_count ?? 0;
  const topLang =
    stats?.languages && stats.languages.length > 0
      ? stats.languages[0].language.toUpperCase()
      : "-";
  const topIntent =
    stats?.intents && stats.intents.length > 0
      ? stats.intents[0].intent
      : "-";

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(5, 1fr)",
        gap: "16px",
        gridColumn: "1 / -1",
      }}
    >
      <StatCard value={total} label="Total Conversations" color="accent" />
      <StatCard value={avgLatency} label="Avg Latency (ms)" color="green" />
      <StatCard value={todayCount} label="Today" color="blue" />
      <StatCard value={topLang} label="Top Language" color="orange" />
      <StatCard value={topIntent} label="Top Intent" />
    </div>
  );
}
