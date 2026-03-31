interface ZoneLabelProps {
  label: string;
  left: number;
  top: number;
}

export function ZoneLabel({ label, left, top }: ZoneLabelProps) {
  return (
    <div
      style={{
        position: "absolute",
        left,
        top,
        transform: "translateZ(8px)",
        fontSize: 17,
        color: "rgba(225,235,255,.85)",
        letterSpacing: "0.12em",
        textTransform: "uppercase",
        padding: "6px 10px",
        borderRadius: 999,
        background: "rgba(9,15,28,.55)",
        border: "1px solid rgba(255,255,255,.08)",
        boxShadow: "0 10px 24px rgba(0,0,0,.25)",
        whiteSpace: "nowrap",
      }}
    >
      {label}
    </div>
  );
}
