import { useTranslation } from "react-i18next";
import { GlassCard } from "./GlassCard";

interface DemoButton {
  label: string;
  color: string;
  hoverColor: string;
  onClick: () => void;
}

interface ControlPanelProps {
  buttons: DemoButton[];
}

function CollapsedControls() {
  const { t } = useTranslation("office");
  return (
    <span style={{ fontSize: 13, color: "var(--lo-muted)", opacity: 0.7 }}>
      {t("livingOffice.hud.controlExpand")}
    </span>
  );
}

export function ControlPanel({ buttons }: ControlPanelProps) {
  const { t } = useTranslation("office");

  const legendItems = [
    { color: "var(--lo-good)", label: t("livingOffice.hud.legendIdle") },
    { color: "var(--lo-cyan)", label: t("livingOffice.hud.legendBusy") },
    { color: "var(--lo-bad)", label: t("livingOffice.hud.legendBlocked") },
    { color: "var(--lo-warn)", label: t("livingOffice.hud.legendHeartbeat") },
    { color: "var(--lo-violet)", label: t("livingOffice.hud.legendCron") },
  ];

  return (
    <GlassCard
      tag={t("livingOffice.hud.controlTag")}
      title={t("livingOffice.hud.controlTitle")}
      storageKey="lo-hud-control"
      collapsedContent={<CollapsedControls />}
    >
      <div style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>
        {buttons.map((btn) => (
          <button
            key={btn.label}
            type="button"
            onClick={btn.onClick}
            style={{
              padding: "3px 8px",
              fontSize: 13,
              fontWeight: 600,
              border: "none",
              borderRadius: 6,
              background: btn.color,
              color: "#fff",
              cursor: "pointer",
              whiteSpace: "nowrap",
              transition: "background 0.15s, transform 0.1s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = btn.hoverColor;
              e.currentTarget.style.transform = "scale(1.05)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = btn.color;
              e.currentTarget.style.transform = "scale(1)";
            }}
          >
            {btn.label}
          </button>
        ))}
      </div>

      <div style={{ display: "flex", gap: 8, marginTop: 5, flexWrap: "wrap" }}>
        {legendItems.map((item) => (
          <div key={item.label} style={{ display: "flex", alignItems: "center", gap: 3 }}>
            <span
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: item.color,
                flexShrink: 0,
              }}
            />
            <span style={{ fontSize: 11, color: "var(--lo-muted)" }}>{item.label}</span>
          </div>
        ))}
      </div>
    </GlassCard>
  );
}
