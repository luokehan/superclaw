import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useCronStore } from "@/store/console-stores/cron-store";
import { GlassPanel } from "./GlassPanel";
import { PanelHead } from "./PanelHead";

interface CronBoardProps {
  tasks?: Array<{ name: string; status: string }>;
}

export function CronBoard({ tasks }: CronBoardProps) {
  const { t } = useTranslation("office");
  const cronTasks = useCronStore((s) => s.tasks);
  const defaultTasks = tasks ?? [
    { name: "09:20 订单看板汇总", status: "scheduled" },
    { name: "10:00 线索清洗广播", status: "scheduled" },
    { name: "11:30 回款提醒", status: "scheduled" },
  ];
  const liveTasks = useMemo(
    () =>
      cronTasks.map((task) => ({
        name: task.name,
        status: task.state.runningAtMs
          ? "running"
          : !task.enabled
            ? "paused"
            : task.state.lastRunStatus ?? "scheduled",
      })),
    [cronTasks],
  );
  const displayTasks = liveTasks.length > 0 ? liveTasks : defaultTasks;

  return (
    <GlassPanel
      style={{
        position: "absolute",
        left: 1068,
        top: 38,
        width: 344,
        height: 214,
        transform: "translateZ(16px)",
      }}
    >
      <PanelHead title={t("livingOffice.panels.cronTitle")} subtitle={t("livingOffice.panels.cronSubtitle")} />
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 7,
          padding: "0 14px 14px",
        }}
      >
        {displayTasks.slice(0, 3).map((task) => (
          <MiniRow key={task.name} left={task.name} right={task.status} />
        ))}
      </div>
    </GlassPanel>
  );
}

function MiniRow({ left, right }: { left: string; right: string }) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        gap: 10,
        fontSize: 16,
        padding: "7px 9px",
        background: "rgba(255,255,255,.04)",
        borderRadius: 10,
      }}
    >
      <span style={{ color: "#e6eefc" }}>{left}</span>
      <span style={{ color: "var(--lo-muted)" }}>{right}</span>
    </div>
  );
}
