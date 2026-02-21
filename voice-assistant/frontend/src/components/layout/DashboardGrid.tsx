import type { ReactNode } from "react";
import styles from "./DashboardGrid.module.css";

export function DashboardGrid({ children }: { children: ReactNode }) {
  return <main className={styles.grid}>{children}</main>;
}

export function FullWidth({ children }: { children: ReactNode }) {
  return <div className={styles.fullWidth}>{children}</div>;
}
