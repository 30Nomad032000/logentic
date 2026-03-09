import { useDashboard } from "../../context/DashboardContext";
import { Card } from "@/components/common/Card";
import { cn } from "@/lib/utils";

export function ComponentHealth() {
  const { health } = useDashboard();
  const components = health?.components;

  return (
    <Card title="Component Health">
      <div className="grid grid-cols-2 gap-2">
        {components ? (
          Object.entries(components).map(([name, status]) => {
            const isOk = status !== "not loaded";
            return (
              <div
                key={name}
                className="flex items-center justify-between py-[11px] px-3.5 bg-[#211f1d] rounded-lg border border-transparent transition-[border-color,background] duration-200 hover:border-[rgba(255,200,120,0.12)] hover:bg-[rgba(33,31,29,0.9)]"
              >
                <span className="font-mono text-[11.5px] font-medium tracking-[0.03em] text-[#a09a8e]">
                  {name.toUpperCase()}
                </span>
                <span
                  className={cn(
                    "font-mono text-[10.5px] px-2.5 py-[3px] rounded-full font-semibold tracking-[0.03em]",
                    isOk
                      ? "bg-[rgba(92,185,122,0.1)] text-[#5cb97a]"
                      : "bg-[rgba(212,154,78,0.1)] text-[#d49a4e]"
                  )}
                >
                  {status}
                </span>
              </div>
            );
          })
        ) : (
          <div className="flex items-center justify-between py-[11px] px-3.5 bg-[#211f1d] rounded-lg border border-transparent">
            <span className="font-mono text-[11.5px] font-medium tracking-[0.03em] text-[#a09a8e]">
              Loading...
            </span>
            <span className="font-mono text-[10.5px] px-2.5 py-[3px] rounded-full font-semibold tracking-[0.03em] bg-[rgba(212,154,78,0.1)] text-[#d49a4e]">
              ...
            </span>
          </div>
        )}
      </div>
    </Card>
  );
}
