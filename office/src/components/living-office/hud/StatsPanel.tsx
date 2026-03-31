import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useProjectionStore } from "@/perception/projection-store";
import { GlassCard } from "./GlassCard";

function CollapsedStats({ stats }: { stats: { label: string; value: number; color: string }[] }) {
  return (
    <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
      {stats.map((s) => (
        <span key={s.label} style={{ display: "inline-flex", alignItems: "center", gap: 3 }}>
          <span
            style={{
              width: 5,
              height: 5,
              borderRadius: "50%",
              background: s.color,
              flexShrink: 0,
            }}
          />
          <span style={{ fontSize: 13, color: "var(--lo-muted)" }}>{s.label}</span>
          <span style={{ fontSize: 14, fontWeight: 700, color: s.color }}>{s.value}</span>
        </span>
      ))}
    </div>
  );
}

export function StatsPanel() {
  const { t } = useTranslation("office");
  const agents = useProjectionStore((s) => s.agents);
  const cronTasks = useProjectionStore((s) => s.sceneArea.cronTasks);

  const activeCount = useMemo(() => {
    let count = 0;
    for (const agent of agents.values()) {
      if (agent.state !== "IDLE" && agent.state !== "DONE") count++;
    }
    return count;
  }, [agents]);

  const pendingCount = useMemo(() => {
    let count = 0;
    for (const agent of agents.values()) {
      if (agent.taskSummary) count++;
    }
    return count;
  }, [agents]);

  const stats = [
    { label: t("livingOffice.hud.statsActive"), value: activeCount, color: "var(--lo-cyan)" },
    { label: t("livingOffice.hud.statsPending"), value: pendingCount, color: "var(--lo-warn)" },
    { label: t("livingOffice.hud.statsCron"), value: cronTasks.length, color: "var(--lo-violet)" },
  ];

  return (
    <GlassCard
      title={t("livingOffice.hud.statsTitle")}
      storageKey="lo-hud-stats"
      defaultCollapsed
      collapsedContent={<CollapsedStats stats={stats} />}
    >
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 4 }}>
        {stats.map((s) => (
          <div key={s.label} style={{ textAlign: "center" }}>
            <div style={{ fontSize: 30, fontWeight: 700, color: s.color, lineHeight: 1.1 }}>
              {s.value}
            </div>
            <div style={{ fontSize: 13, color: "var(--lo-muted)", marginTop: 2 }}>{s.label}</div>
          </div>
        ))}
      </div>
    </GlassCard>
  );
}
