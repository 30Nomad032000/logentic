export function Spinner() {
  return (
    <div
      style={{
        display: "inline-block",
        width: "16px",
        height: "16px",
        border: "2px solid var(--border)",
        borderTopColor: "var(--accent)",
        borderRadius: "50%",
        animation: "spin 0.8s linear infinite",
      }}
    />
  );
}
