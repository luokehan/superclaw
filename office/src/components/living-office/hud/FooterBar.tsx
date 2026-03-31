import type { ReactNode } from "react";

interface FooterBarProps {
  left?: ReactNode;
  right?: ReactNode;
}

export function FooterBar({ left, right }: FooterBarProps) {
  return (
    <div
      className="lo-footer-bar"
      style={{
        position: "absolute",
        bottom: 10,
        left: 14,
        right: 14,
        zIndex: 21,
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: 10,
        pointerEvents: "none",
        alignItems: "stretch",
      }}
    >
      {left && <div style={{ pointerEvents: "auto" }}>{left}</div>}
      {right && <div style={{ pointerEvents: "auto" }}>{right}</div>}
    </div>
  );
}
