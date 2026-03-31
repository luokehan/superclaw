import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import i18n from "@/i18n";
import { useProjectionStore } from "@/perception/projection-store";
import { GlassCard } from "./GlassCard";

function formatTime(ts: number): string {
  const d = new Date(ts);
  const locale = i18n.language === "zh" ? "zh-CN" : "en-US";
  return d.toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function LogCount({ count }: { count: number }) {
  const { t } = useTranslation("office");
  return (
    <span style={{ fontSize: 13, color: "var(--lo-muted)", opacity: 0.8 }}>
      {t("livingOffice.hud.eventLogCount", { count })}
    </span>
  );
}

function CollapsedLog({ text }: { text: string }) {
  return (
    <span
      style={{
        fontSize: 13,
        color: "var(--lo-muted)",
        overflow: "hidden",
        textOverflow: "ellipsis",
        whiteSpace: "nowrap",
      }}
    >
      {text}
    </span>
  );
}

export function EventLogPanel() {
  const { t } = useTranslation("office");
  const narrativeLogs = useProjectionStore((s) => s.narrativeLogs);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [narrativeLogs]);

  const latestText = narrativeLogs.length > 0
    ? narrativeLogs[narrativeLogs.length - 1].text
    : t("livingOffice.hud.eventLogWaiting");

  return (
    <GlassCard
      tag={t("livingOffice.hud.eventLogTag")}
      title={t("livingOffice.hud.eventLogTitle")}
      headerExtra={<LogCount count={narrativeLogs.length} />}
      storageKey="lo-hud-log"
      defaultCollapsed
      collapsedContent={<CollapsedLog text={latestText} />}
    >
      <div
        ref={scrollRef}
        style={{
          maxHeight: 42,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: 2,
          scrollbarWidth: "none",
        }}
      >
        {narrativeLogs.length === 0 ? (
          <div style={{ fontSize: 14, color: "var(--lo-muted)", opacity: 0.5, fontStyle: "italic" }}>
            {t("livingOffice.hud.eventLogWaiting")}
          </div>
        ) : (
          narrativeLogs.map((log, i) => (
            <div
              key={`${String(log.ts)}-${String(i)}`}
              style={{ display: "flex", gap: 8, fontSize: 14, lineHeight: 1.4 }}
            >
              <span
                style={{
                  color: "var(--lo-muted)",
                  opacity: 0.6,
                  flexShrink: 0,
                  fontFamily: "monospace",
                  fontSize: 13,
                }}
              >
                {formatTime(log.ts)}
              </span>
              <span
                style={{
                  color: "var(--lo-text)",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {log.text}
              </span>
            </div>
          ))
        )}
      </div>
    </GlassCard>
  );
}
