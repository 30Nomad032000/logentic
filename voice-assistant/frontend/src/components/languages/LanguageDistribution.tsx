import { useDashboard } from "../../context/DashboardContext";
import { Card } from "@/components/common/Card";
import { EmptyState } from "@/components/common/EmptyState";

export function LanguageDistribution() {
  const { stats } = useDashboard();
  const languages = stats?.languages;

  if (!languages || languages.length === 0) {
    return (
      <Card title="Language Distribution">
        <EmptyState message="No data yet" />
      </Card>
    );
  }

  const maxCount = languages[0].count;

  return (
    <Card title="Language Distribution">
      <div className="flex flex-col gap-2.5">
        {languages.map((l) => (
          <div key={l.language} className="flex items-center gap-3">
            <span className="w-8 font-mono text-[11px] font-bold uppercase text-[#e8a44a] tracking-[0.04em]">
              {l.language}
            </span>
            <div className="flex-1 h-[22px] bg-[#211f1d] rounded-md overflow-hidden">
              <div
                className="h-full bg-[rgba(232,164,74,0.15)] border-l-[3px] border-l-[#e8a44a] rounded-md transition-[width] duration-[600ms] ease-[cubic-bezier(0.34,1.56,0.64,1)] flex items-center pl-2.5 font-mono text-[11px] font-semibold text-[#e8a44a] min-w-fit"
                style={{ width: `${(l.count / maxCount) * 100}%` }}
              >
                {l.count}
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
