import type { CSSProperties, ReactNode } from "react";
import type { ZoneConfig } from "../types";

interface ZonePanelProps {
  config: ZoneConfig;
  children?: ReactNode;
  className?: string;
  style?: CSSProperties;
}

export function ZonePanel({ config, children, className = "", style }: ZonePanelProps) {
  return (
    <div
      className={className}
      style={{
        position: "absolute",
        left: config.position.left,
        top: config.position.top,
        width: config.size.width,
        height: config.size.height,
        borderRadius: 26,
        border: "1px solid rgba(255,255,255,.06)",
        background:
          "linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.015))",
        boxShadow:
          "inset 0 1px 0 rgba(255,255,255,.05), 0 16px 40px rgba(0,0,0,.28)",
        transform: "translateZ(4px)",
        ...style,
      }}
    >
      {children}
    </div>
  );
}
