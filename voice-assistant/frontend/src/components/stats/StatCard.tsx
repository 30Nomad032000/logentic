import { cn } from "@/lib/utils";

interface StatCardProps {
  value: string | number;
  label: string;
  color?: "accent" | "green" | "blue" | "orange";
  delay?: number;
}

const valueColorMap: Record<string, string> = {
  accent: "text-[#e8a44a]",
  green: "text-[#5cb97a]",
  blue: "text-[#5a9ec4]",
  orange: "text-[#d49a4e]",
};

const beforeGradientMap: Record<string, string> = {
  accent: "before:bg-gradient-to-r before:from-transparent before:via-[#e8a44a] before:to-transparent",
  green: "before:bg-gradient-to-r before:from-transparent before:via-[#5cb97a] before:to-transparent",
  blue: "before:bg-gradient-to-r before:from-transparent before:via-[#5a9ec4] before:to-transparent",
  orange: "before:bg-gradient-to-r before:from-transparent before:via-[#d49a4e] before:to-transparent",
};

export function StatCard({ value, label, color, delay = 0 }: StatCardProps) {
  return (
    <div
      className={cn(
        "bg-[rgba(26,25,23,0.7)] backdrop-blur-[12px] border border-[rgba(255,200,120,0.06)] rounded-xl px-[18px] py-5 text-center shadow-[0_1px_3px_rgba(0,0,0,0.3),0_8px_24px_rgba(0,0,0,0.15)] transition-[transform,border-color,box-shadow] duration-[250ms] ease-in-out hover:-translate-y-0.5 hover:border-[rgba(255,200,120,0.12)] hover:shadow-[0_4px_12px_rgba(0,0,0,0.4),0_12px_32px_rgba(0,0,0,0.2)] animate-[fadeInUp_0.5s_ease_both] relative overflow-hidden",
        "before:content-[''] before:absolute before:top-0 before:left-1/2 before:-translate-x-1/2 before:w-[40%] before:h-px before:rounded-b-sm before:opacity-0 before:transition-opacity before:duration-[250ms] hover:before:opacity-100",
        color && beforeGradientMap[color]
      )}
      style={{ animationDelay: `${delay}ms` }}
    >
      <div
        className={cn(
          "font-mono text-[30px] font-bold text-[#ede9e1] leading-none tracking-[-0.02em]",
          color && valueColorMap[color]
        )}
      >
        {value}
      </div>
      <div className="font-mono text-[10px] font-medium text-[#8a8478] mt-2 uppercase tracking-[0.08em]">
        {label}
      </div>
    </div>
  );
}
