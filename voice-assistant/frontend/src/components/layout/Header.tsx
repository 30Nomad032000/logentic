import { useDashboard } from "../../context/DashboardContext";
import { cn } from "@/lib/utils";

export function Header() {
  const { health, error } = useDashboard();
  const isOnline = health !== null && error === null;
  const version = health?.version ?? "0.2.0";

  return (
    <header className="sticky top-0 z-50 backdrop-blur-[16px] bg-[rgba(17,17,16,0.85)]">
      <div className="h-0.5 bg-gradient-to-r from-[#e8a44a] via-[rgba(232,164,74,0.3)] to-transparent" />
      <div className="px-9 py-3.5 flex items-center justify-between border-b border-[rgba(255,200,120,0.06)]">
        <div className="flex items-center gap-3.5">
          <div className="w-[38px] h-[38px] rounded-lg bg-[rgba(232,164,74,0.15)] border border-[rgba(232,164,74,0.15)] flex items-center justify-center text-[#e8a44a]">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" x2="12" y1="19" y2="22" />
            </svg>
          </div>
          <div className="flex items-baseline gap-2.5">
            <h1 className="font-display text-[22px] font-normal text-[#ede9e1] tracking-[-0.01em]">Logentic</h1>
            <span className="font-mono text-[11px] font-normal text-[#8a8478] tracking-[0.04em] uppercase">Voice Assistant</span>
          </div>
        </div>
        <div className="flex items-center gap-3.5">
          <span className="font-mono text-[11px] font-medium text-[#8a8478] px-2.5 py-1 border border-[rgba(255,200,120,0.06)] rounded-full">
            v{version}
          </span>
          <div className="flex items-center gap-2 py-[5px] pl-2.5 pr-3.5 rounded-full bg-[rgba(26,25,23,0.7)] border border-[rgba(255,200,120,0.06)]">
            <span
              className={cn(
                "w-[7px] h-[7px] rounded-full",
                isOnline
                  ? "bg-[#5cb97a] shadow-[0_0_8px_rgba(92,185,122,0.5)] animate-[pulse_2.5s_ease-in-out_infinite]"
                  : "bg-[#d4564e] shadow-[0_0_8px_rgba(212,86,78,0.5)]"
              )}
            />
            <span className="font-mono text-[11px] font-medium text-[#a09a8e] tracking-[0.03em]">
              {isOnline ? "Online" : "Offline"}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
