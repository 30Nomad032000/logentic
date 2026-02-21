import { useDashboard } from "../../context/DashboardContext";
import { Card } from "../common/Card";
import styles from "./ComponentHealth.module.css";

export function ComponentHealth() {
  const { health } = useDashboard();
  const components = health?.components;

  return (
    <Card title="Component Health">
      <div className={styles.grid}>
        {components ? (
          Object.entries(components).map(([name, status]) => {
            const isOk = status !== "not loaded";
            return (
              <div key={name} className={styles.item}>
                <span className={styles.name}>{name.toUpperCase()}</span>
                <span
                  className={`${styles.status} ${isOk ? styles.ok : styles.warn}`}
                >
                  {status}
                </span>
              </div>
            );
          })
        ) : (
          <div className={styles.item}>
            <span className={styles.name}>Loading...</span>
            <span className={`${styles.status} ${styles.warn}`}>...</span>
          </div>
        )}
      </div>
    </Card>
  );
}
