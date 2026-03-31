import type { ReactNode } from "react";

interface HudBarProps {
  left?: ReactNode;
  center?: ReactNode;
  right?: ReactNode;
}

export function HudBar({ left, center, right }: HudBarProps) {
  return (
    <div
      className="lo-hud-bar"
      style={{
        position: "absolute",
        top: 8,
        left: 8,
        right: 8,
        zIndex: 20,
        display: "grid",
        gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1fr)",
        gap: 8,
        pointerEvents: "none",
        alignItems: "start",
      }}
    >
      {left && <div style={{ pointerEvents: "auto", minWidth: 0, overflow: "hidden" }}>{left}</div>}
      {center && <div style={{ pointerEvents: "auto", minWidth: 0, overflow: "hidden" }}>{center}</div>}
      {right && <div style={{ pointerEvents: "auto", minWidth: 0, overflow: "hidden" }}>{right}</div>}
    </div>
  );
}
