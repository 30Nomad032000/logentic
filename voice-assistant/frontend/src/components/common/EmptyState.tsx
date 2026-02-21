interface EmptyStateProps {
  message: string;
}

export function EmptyState({ message }: EmptyStateProps) {
  return (
    <div
      style={{
        textAlign: "center",
        padding: "40px",
        color: "var(--text-dim)",
        fontSize: "13px",
      }}
    >
      {message}
    </div>
  );
}
