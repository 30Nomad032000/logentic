import styles from "./LatencyBar.module.css";

interface LatencyBarProps {
  label: string;
  ms: number;
  maxMs: number;
  variant: "asr" | "translation" | "llm" | "tts";
}

export function LatencyBar({ label, ms, maxMs, variant }: LatencyBarProps) {
  const pct = maxMs > 0 ? (ms / maxMs) * 100 : 0;
  return (
    <div className={styles.item}>
      <span className={styles.label}>{label}</span>
      <div className={styles.barBg}>
        <div
          className={`${styles.bar} ${styles[variant]}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={styles.value}>
        {ms > 0 ? `${Math.round(ms)}ms` : "-"}
      </span>
    </div>
  );
}
