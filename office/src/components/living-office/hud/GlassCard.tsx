import { useState, type CSSProperties, type ReactNode } from "react";

interface GlassCardProps {
  children: ReactNode;
  style?: CSSProperties;
  tag?: string;
  /** Collapsible title — when set, the card becomes collapsible */
  title?: string;
  /** Content rendered inline in the collapsed bar (replaces subtitle) */
  collapsedContent?: ReactNode;
  /** Extra element rendered at the right end of header row */
  headerExtra?: ReactNode;
  /** localStorage key for persisting collapsed state */
  storageKey?: string;
  /** Start collapsed */
  defaultCollapsed?: boolean;
}

function readCollapsed(key: string | undefined, fallback: boolean): boolean {
  if (!key) return fallback;
  try {
    const v = localStorage.getItem(key);
    if (v === "1") return true;
    if (v === "0") return false;
  } catch {
    /* noop */
  }
  return fallback;
}

const COLLAPSED_H = 34;

export function GlassCard({
  children,
  style,
  tag,
  title,
  collapsedContent,
  headerExtra,
  storageKey,
  defaultCollapsed = false,
}: GlassCardProps) {
  const [collapsed, setCollapsed] = useState(() =>
    readCollapsed(storageKey, defaultCollapsed),
  );

  const isCollapsible = Boolean(title);

  const toggle = () => {
    const next = !collapsed;
    setCollapsed(next);
    if (storageKey) {
      try {
        localStorage.setItem(storageKey, next ? "1" : "0");
      } catch {
        /* noop */
      }
    }
  };

  return (
    <div
      style={{
        background: "var(--lo-glass-bg)",
        backdropFilter: "var(--lo-glass-blur)",
        WebkitBackdropFilter: "var(--lo-glass-blur)",
        border: "var(--lo-glass-border)",
        borderRadius: collapsed ? 10 : "var(--lo-glass-radius)",
        padding: collapsed ? "0 10px" : "10px 14px",
        height: collapsed ? COLLAPSED_H : undefined,
        minHeight: collapsed ? COLLAPSED_H : undefined,
        position: "relative",
        overflow: "hidden",
        minWidth: 0,
        display: "flex",
        flexDirection: "column",
        transition: "padding 0.18s ease, border-radius 0.18s ease, height 0.18s ease",
        ...style,
      }}
    >
      {/* Tag label (top-right) — only when expanded */}
      {tag && !collapsed && (
        <div
          style={{
            position: "absolute",
            top: 8,
            right: 10,
            fontSize: 13,
            fontWeight: 600,
            letterSpacing: "0.04em",
            textTransform: "uppercase",
            color: "var(--lo-muted)",
            opacity: 0.6,
          }}
        >
          {tag}
        </div>
      )}

      {/* Collapsible header bar */}
      {isCollapsible && (
        <div
          onClick={toggle}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") toggle(); }}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 5,
            cursor: "pointer",
            userSelect: "none",
            height: collapsed ? COLLAPSED_H : "auto",
            minHeight: collapsed ? COLLAPSED_H : undefined,
          }}
        >
          {/* Chevron */}
          <span
            style={{
              display: "inline-flex",
              width: 10,
              height: 10,
              alignItems: "center",
              justifyContent: "center",
              fontSize: 10,
              color: "var(--lo-muted)",
              opacity: 0.6,
              transition: "transform 0.18s ease",
              transform: collapsed ? "rotate(-90deg)" : "rotate(0deg)",
              flexShrink: 0,
            }}
          >
            ▼
          </span>

          {/* Title */}
          <span
            style={{
              fontSize: collapsed ? 11 : 13,
              fontWeight: 600,
              color: "var(--lo-text)",
              flexShrink: 0,
              whiteSpace: "nowrap",
              transition: "font-size 0.15s ease",
            }}
          >
            {title}
          </span>

          {/* Collapsed inline content — fills the middle space */}
          {collapsed && collapsedContent && (
            <div
              style={{
                flex: 1,
                minWidth: 0,
                overflow: "hidden",
                display: "flex",
                alignItems: "center",
              }}
              onClick={(e) => e.stopPropagation()}
            >
              {collapsedContent}
            </div>
          )}

          {/* Right-end extras */}
          {headerExtra && (
            <div style={{ marginLeft: collapsed && !collapsedContent ? "auto" : 0, flexShrink: 0 }}>
              {headerExtra}
            </div>
          )}

          {/* Tag (collapsed only) */}
          {tag && collapsed && (
            <span
              style={{
                marginLeft: headerExtra ? 4 : "auto",
                fontSize: 10,
                fontWeight: 600,
                letterSpacing: "0.04em",
                textTransform: "uppercase",
                color: "var(--lo-muted)",
                opacity: 0.4,
                flexShrink: 0,
              }}
            >
              {tag}
            </span>
          )}
        </div>
      )}

      {/* Expanded content body */}
      {!collapsed && (
        <div style={{ marginTop: isCollapsible ? 4 : 0, flex: 1, minHeight: 0 }}>
          {children}
        </div>
      )}
    </div>
  );
}
