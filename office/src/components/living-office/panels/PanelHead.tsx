interface PanelHeadProps {
  title: string;
  subtitle?: string;
}

export function PanelHead({ title, subtitle }: PanelHeadProps) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "12px 14px 8px",
      }}
    >
      <b style={{ fontSize: 18, color: "#e9f2ff" }}>{title}</b>
      {subtitle && (
        <span style={{ fontSize: 16, color: "var(--lo-muted)" }}>
          {subtitle}
        </span>
      )}
    </div>
  );
}
