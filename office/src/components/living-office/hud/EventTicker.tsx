import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useProjectionStore } from "@/perception/projection-store";
import { GlassCard } from "./GlassCard";

function CollapsedTicker({ items }: { items: { title: string; desc: string }[] }) {
  const latest = items[items.length - 1];
  if (!latest) return null;

  return (
    <div
      style={{
        display: "flex",
        gap: 6,
        overflow: "hidden",
        alignItems: "center",
        maskImage: "linear-gradient(90deg, #000 85%, transparent 100%)",
        WebkitMaskImage: "linear-gradient(90deg, #000 85%, transparent 100%)",
      }}
    >
      <span style={{ fontSize: 13, fontWeight: 600, color: "var(--lo-cyan)", flexShrink: 0 }}>
        {latest.title}
      </span>
      <span
        style={{
          fontSize: 13,
          color: "var(--lo-muted)",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        {latest.desc}
      </span>
    </div>
  );
}

export function EventTicker() {
  const { t } = useTranslation("office");
  const narrativeLogs = useProjectionStore((s) => s.narrativeLogs);

  const fallbackItems = useMemo(() => [
    { title: t("livingOffice.fallbackEvents.msgArrival"), desc: t("livingOffice.fallbackEvents.msgArrivalDesc") },
    { title: t("livingOffice.fallbackEvents.gmDispatch"), desc: t("livingOffice.fallbackEvents.gmDispatchDesc") },
    { title: t("livingOffice.fallbackEvents.salesReport"), desc: t("livingOffice.fallbackEvents.salesReportDesc") },
    { title: t("livingOffice.fallbackEvents.cronBroadcast"), desc: t("livingOffice.fallbackEvents.cronBroadcastDesc") },
    { title: t("livingOffice.fallbackEvents.heartbeat"), desc: t("livingOffice.fallbackEvents.heartbeatDesc") },
    { title: t("livingOffice.fallbackEvents.subAgentCollab"), desc: t("livingOffice.fallbackEvents.subAgentCollabDesc") },
  ], [t]);

  const items = useMemo(() => {
    if (narrativeLogs.length >= 3) {
      return narrativeLogs.slice(-6).map((log) => ({
        title: log.kind.replace(/_/g, " "),
        desc: log.text,
      }));
    }
    return fallbackItems;
  }, [narrativeLogs, fallbackItems]);

  const doubled = useMemo(() => [...items, ...items], [items]);

  return (
    <GlassCard
      tag={t("livingOffice.hud.tickerTag")}
      title={t("livingOffice.hud.tickerTitle")}
      storageKey="lo-hud-ticker"
      collapsedContent={<CollapsedTicker items={items} />}
    >
      <div style={{ fontSize: 14, color: "var(--lo-muted)", marginBottom: 4 }}>
        {t("livingOffice.hud.tickerSubtitle")}
      </div>

      <div
        style={{
          height: 44,
          overflow: "hidden",
          position: "relative",
          maskImage: "linear-gradient(180deg, transparent, #000 15%, #000 85%, transparent)",
          WebkitMaskImage: "linear-gradient(180deg, transparent, #000 15%, #000 85%, transparent)",
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 6,
            animation: "lo-ticker-scroll 14s linear infinite",
          }}
        >
          {doubled.map((item, i) => (
            <div
              key={`${item.title}-${String(i)}`}
              style={{ display: "flex", gap: 8, alignItems: "baseline", whiteSpace: "nowrap" }}
            >
              <span
                style={{
                  fontSize: 14,
                  fontWeight: 600,
                  color: "var(--lo-cyan)",
                  flexShrink: 0,
                }}
              >
                {item.title}
              </span>
              <span
                style={{
                  fontSize: 14,
                  color: "var(--lo-muted)",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {item.desc}
              </span>
            </div>
          ))}
        </div>
      </div>
    </GlassCard>
  );
}
