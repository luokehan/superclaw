import { useMemo } from "react";
import { useProjectionStore } from "@/perception/projection-store";
import { useOfficeStore } from "@/store/office-store";
import { GlassPanel } from "./GlassPanel";
import { PanelHead } from "./PanelHead";

interface ProjectRoomProps {
  tasks?: Array<{ title: string; subtitle: string }>;
}

export function ProjectRoom({ tasks }: ProjectRoomProps) {
  const defaultTasks = tasks ?? [
    { title: "等待任务中...", subtitle: "通过 Telegram 发送任务给 SuperClaw" },
  ];
  const lastSessionsSnapshot = useOfficeStore((s) => s.lastSessionsSnapshot);
  const projectedTasks = useProjectionStore((s) => s.sceneArea.projectTasks);
  const sessions = lastSessionsSnapshot?.sessions;
  const liveTasks =
    sessions && sessions.length > 0
      ? sessions.map((session) => ({
          title: session.label || session.agentId,
          subtitle: session.task || session.requesterSessionKey,
        }))
      : projectedTasks;
  const displayTasks = useMemo(
    () => (liveTasks.length > 0 ? liveTasks : defaultTasks),
    [liveTasks, defaultTasks],
  );

  return (
    <GlassPanel
      style={{
        position: "absolute",
        left: 1068,
        top: 308,
        width: 344,
        height: 130,
        transform: "translateZ(16px)",
      }}
    >
      <PanelHead title="当前任务" subtitle="SuperClaw 工作队列" />
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 8,
          padding: "0 14px 14px",
        }}
      >
        {displayTasks.slice(0, 3).map((task) => (
          <div
            key={task.title}
            style={{
              padding: "8px 10px",
              borderRadius: 12,
              background: "rgba(255,255,255,.04)",
              border: "1px solid rgba(255,255,255,.05)",
              fontSize: 16,
              color: "#e6eefc",
            }}
          >
            {task.title}
            <small
              style={{ color: "var(--lo-muted)", display: "block", marginTop: 3 }}
            >
              {task.subtitle}
            </small>
          </div>
        ))}
      </div>
    </GlassPanel>
  );
}
