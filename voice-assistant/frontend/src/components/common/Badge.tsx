import { cn } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "accent" | "green" | "red" | "orange";
}

const variantClasses: Record<string, string> = {
  accent: "bg-[rgba(232,164,74,0.15)] text-[#e8a44a]",
  green: "bg-[rgba(92,185,122,0.1)] text-[#5cb97a]",
  red: "bg-[rgba(212,86,78,0.1)] text-[#d4564e]",
  orange: "bg-[rgba(212,154,78,0.1)] text-[#d49a4e]",
};

export function Badge({ children, variant = "accent" }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-[3px] rounded-full font-mono text-[10.5px] font-semibold tracking-[0.04em]",
        variantClasses[variant]
      )}
    >
      {children}
    </span>
  );
}
