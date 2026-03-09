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
    <div className="grid grid-cols-5 gap-4 col-span-full">
      <StatCard value={total} label="Conversations" color="accent" delay={0} />
      <StatCard value={avgLatency} label="Avg Latency ms" color="green" delay={60} />
      <StatCard value={todayCount} label="Today" color="blue" delay={120} />
      <StatCard value={topLang} label="Top Language" color="orange" delay={180} />
      <StatCard value={topIntent} label="Top Intent" delay={240} />
    </div>
  );
}
