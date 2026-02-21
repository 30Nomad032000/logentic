interface BadgeProps {
  children: React.ReactNode;
  variant?: "accent" | "green" | "red" | "orange";
}

const variantStyles: Record<string, React.CSSProperties> = {
  accent: {
    background: "var(--accent-glow)",
    color: "var(--accent)",
  },
  green: {
    background: "rgba(34,197,94,0.12)",
    color: "var(--green)",
  },
  red: {
    background: "rgba(239,68,68,0.12)",
    color: "var(--red)",
  },
  orange: {
    background: "rgba(245,158,11,0.12)",
    color: "var(--orange)",
  },
};

export function Badge({ children, variant = "accent" }: BadgeProps) {
  return (
    <span
      style={{
        ...variantStyles[variant],
        padding: "2px 8px",
        borderRadius: "6px",
        fontSize: "12px",
        fontWeight: 500,
      }}
    >
      {children}
    </span>
  );
}
