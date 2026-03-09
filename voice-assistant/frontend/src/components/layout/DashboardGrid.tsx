import type { ReactNode } from "react";

export function DashboardGrid({ children }: { children: ReactNode }) {
  return (
    <main className="grid grid-cols-2 gap-[22px] px-9 pt-7 pb-12 max-w-[1440px] mx-auto animate-[fadeIn_0.4s_ease] max-[900px]:grid-cols-1 max-[900px]:px-4 max-[900px]:pt-5 max-[900px]:pb-10">
      {children}
    </main>
  );
}

export function FullWidth({ children }: { children: ReactNode }) {
  return <div className="col-span-full">{children}</div>;
}
