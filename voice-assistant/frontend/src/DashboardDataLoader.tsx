import { createContext, useContext, type ReactNode } from "react";
import { useDashboardData } from "./hooks/useDashboardData";

const RefreshContext = createContext<() => void>(() => {});

export function useRefresh() {
  return useContext(RefreshContext);
}

export function DashboardDataLoader({ children }: { children: ReactNode }) {
  const { refresh } = useDashboardData();
  return (
    <RefreshContext.Provider value={refresh}>{children}</RefreshContext.Provider>
  );
}
