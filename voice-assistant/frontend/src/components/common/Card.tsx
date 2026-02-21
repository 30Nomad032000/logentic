import type { ReactNode } from "react";
import styles from "./Card.module.css";

interface CardProps {
  title?: string;
  children: ReactNode;
  className?: string;
}

export function Card({ title, children, className }: CardProps) {
  return (
    <div className={`${styles.card} ${className ?? ""}`}>
      {title && <div className={styles.title}>{title}</div>}
      {children}
    </div>
  );
}
