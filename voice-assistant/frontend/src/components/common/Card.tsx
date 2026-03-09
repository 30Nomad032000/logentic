import type { ReactNode } from "react";
import {
  Card as ShadcnCard,
  CardHeader,
  CardContent,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface CardProps {
  title?: string;
  children: ReactNode;
  className?: string;
  delay?: number;
}

export function Card({ title, children, className, delay = 0 }: CardProps) {
  return (
    <ShadcnCard
      className={cn(
        "bg-[rgba(26,25,23,0.7)] backdrop-blur-[12px] border-[rgba(255,200,120,0.06)] rounded-xl p-[22px] shadow-[0_1px_3px_rgba(0,0,0,0.3),0_8px_24px_rgba(0,0,0,0.15)] transition-[border-color,box-shadow] duration-[250ms] ease-in-out hover:border-[rgba(255,200,120,0.12)] animate-[fadeInUp_0.5s_ease_both]",
        className
      )}
      style={{ animationDelay: `${delay}ms` }}
    >
      {title && (
        <CardHeader className="p-0 pb-[12px] mb-[18px] border-b border-[rgba(255,200,120,0.06)]">
          <div className="font-mono text-[10.5px] font-semibold text-[#9a9488] uppercase tracking-[0.1em]">
            {title}
          </div>
        </CardHeader>
      )}
      <CardContent className="p-0">{children}</CardContent>
    </ShadcnCard>
  );
}
