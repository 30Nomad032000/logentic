import { useDashboard } from "../../context/DashboardContext";
import { Card } from "../common/Card";
import { EmptyState } from "../common/EmptyState";
import styles from "./LanguageDistribution.module.css";

export function LanguageDistribution() {
  const { stats } = useDashboard();
  const languages = stats?.languages;

  if (!languages || languages.length === 0) {
    return (
      <Card title="Language Distribution">
        <EmptyState message="No data yet" />
      </Card>
    );
  }

  const maxCount = languages[0].count;

  return (
    <Card title="Language Distribution">
      <div className={styles.bars}>
        {languages.map((l) => (
          <div key={l.language} className={styles.row}>
            <span className={styles.code}>{l.language}</span>
            <div className={styles.barBg}>
              <div
                className={styles.bar}
                style={{ width: `${(l.count / maxCount) * 100}%` }}
              >
                {l.count}
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
