import { useDashboard } from "../../context/DashboardContext";
import styles from "./Header.module.css";

export function Header() {
  const { health, error } = useDashboard();
  const isOnline = health !== null && error === null;
  const version = health?.version ?? "0.2.0";

  return (
    <header className={styles.header}>
      <h1 className={styles.title}>
        <span className={`${styles.dot} ${isOnline ? styles.online : styles.offline}`} />
        Voice Assistant Dashboard
      </h1>
      <div className={styles.right}>
        <span className={styles.versionBadge}>v{version}</span>
        <span>{isOnline ? "System Online" : "Offline"}</span>
      </div>
    </header>
  );
}
