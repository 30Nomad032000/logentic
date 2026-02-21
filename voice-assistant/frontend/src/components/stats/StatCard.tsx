import styles from "./StatCard.module.css";

interface StatCardProps {
  value: string | number;
  label: string;
  color?: "accent" | "green" | "blue" | "orange";
}

export function StatCard({ value, label, color }: StatCardProps) {
  const colorClass = color ? styles[color] : "";
  return (
    <div className={`${styles.card} ${colorClass}`}>
      <div className={styles.value}>{value}</div>
      <div className={styles.label}>{label}</div>
    </div>
  );
}
