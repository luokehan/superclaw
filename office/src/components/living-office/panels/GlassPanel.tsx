import type { CSSProperties, ReactNode } from "react";

interface GlassPanelProps {
  children?: ReactNode;
  className?: string;
  style?: CSSProperties;
}

export function GlassPanel({ children, className = "", style }: GlassPanelProps) {
  return (
    <div
      className={className}
      style={{
        borderRadius: 22,
        background:
          "linear-gradient(180deg, rgba(9,16,30,.95), rgba(8,13,25,.88))",
        border: "1px solid rgba(255,255,255,.07)",
        boxShadow: "var(--lo-glow)",
        overflow: "auto",
        ...style,
      }}
    >
      {children}
    </div>
  );
}
