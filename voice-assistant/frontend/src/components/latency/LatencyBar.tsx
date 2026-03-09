import { cn } from "@/lib/utils";

interface LatencyBarProps {
  label: string;
  ms: number;
  maxMs: number;
  variant: "asr" | "translation" | "llm" | "tts";
}

const variantStyles: Record<string, string> = {
  asr: "bg-gradient-to-r from-[#5a9ec4] to-[#7ab8d4] shadow-[0_0_12px_rgba(90,158,196,0.25)]",
  translation: "bg-gradient-to-r from-[#e8a44a] to-[#f0c77a] shadow-[0_0_12px_rgba(232,164,74,0.25)]",
  llm: "bg-gradient-to-r from-[#d49a4e] to-[#e8b874] shadow-[0_0_12px_rgba(212,154,78,0.25)]",
  tts: "bg-gradient-to-r from-[#5cb97a] to-[#8ad4a0] shadow-[0_0_12px_rgba(92,185,122,0.25)]",
};

export function LatencyBar({ label, ms, maxMs, variant }: LatencyBarProps) {
  const pct = maxMs > 0 ? (ms / maxMs) * 100 : 0;
  return (
    <div className="flex items-center gap-3.5 mb-3.5 last:mb-0">
      <span className="w-[90px] font-mono text-[11.5px] font-medium text-[#a09a8e] tracking-[0.02em]">
        {label}
      </span>
      <div className="flex-1 h-2.5 bg-[#211f1d] rounded-[5px] overflow-hidden relative">
        <div
          className={cn(
            "h-full rounded-[5px] transition-[width] duration-700 ease-[cubic-bezier(0.34,1.56,0.64,1)] relative",
            "after:content-[''] after:absolute after:top-0 after:left-0 after:right-0 after:h-1/2 after:bg-gradient-to-b after:from-white/15 after:to-transparent after:rounded-t-[5px]",
            variantStyles[variant]
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-16 text-right font-mono text-xs font-semibold text-[#a09a8e]">
        {ms > 0 ? `${Math.round(ms)}ms` : "-"}
      </span>
    </div>
  );
}
