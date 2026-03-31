import { useMemo } from "react";
import { useProjectionStore } from "@/perception/projection-store";
import type { AgentProjection, NarrativeLog } from "@/perception/types";
import { WORK_ZONES } from "../config";

function useAgent(): AgentProjection | undefined {
  const agents = useProjectionStore((s) => s.agents);
  return agents.values().next().value as AgentProjection | undefined;
}

function useLogs(): NarrativeLog[] {
  return useProjectionStore((s) => s.narrativeLogs);
}

function useToolHistory(logs: NarrativeLog[]): string[] {
  return useMemo(() => {
    const tools: string[] = [];
    for (let i = logs.length - 1; i >= 0 && tools.length < 8; i--) {
      if (logs[i].kind === "CALL_TOOL" && logs[i].text) {
        const name = logs[i].text.length > 24 ? logs[i].text.slice(0, 24) + "…" : logs[i].text;
        if (!tools.includes(name)) tools.push(name);
      }
    }
    return tools;
  }, [logs]);
}

function useRecentActivity(logs: NarrativeLog[]): string[] {
  return useMemo(() => {
    const items: string[] = [];
    for (let i = logs.length - 1; i >= 0 && items.length < 4; i--) {
      if (logs[i].kind !== "POLL_HEARTBEAT" && logs[i].text) {
        const t = logs[i].text.length > 28 ? logs[i].text.slice(0, 28) + "…" : logs[i].text;
        items.push(t);
      }
    }
    return items;
  }, [logs]);
}

// --- Room components ---

function RoomWall({ x, y, w, h, color, label, children }: {
  x: number; y: number; w: number; h: number; color: string; label: string;
  children?: React.ReactNode;
}) {
  const icon = label.split(" ")[0];
  const name = label.split(" ").slice(1).join(" ");

  return (
    <div style={{ position: "absolute", left: x, top: y, width: w, height: h, transform: "translateZ(4px)", pointerEvents: "none" }}>
      <div style={{
        position: "absolute", inset: 0, borderRadius: 22,
        background: `linear-gradient(180deg, ${color}0a, ${color}04 40%, transparent 80%)`,
        border: `1px solid ${color}18`,
        boxShadow: `inset 0 1px 0 ${color}10, 0 12px 32px rgba(0,0,0,.2)`,
      }} />
      {/* Floor */}
      <div style={{
        position: "absolute", left: 10, right: 10, bottom: 10, height: 200, borderRadius: 16,
        background: `repeating-linear-gradient(90deg, ${color}06, ${color}06 1px, transparent 1px, transparent 40px), repeating-linear-gradient(0deg, ${color}04, ${color}04 1px, transparent 1px, transparent 40px)`,
        border: `1px solid ${color}0a`,
      }} />
      {/* Header */}
      <div style={{
        position: "absolute", left: 0, top: 0, width: "100%", padding: "14px 18px",
        display: "flex", alignItems: "center", gap: 10,
        borderRadius: "22px 22px 0 0",
        background: `linear-gradient(90deg, ${color}18, transparent)`,
        borderBottom: `1px solid ${color}15`,
      }}>
        <span style={{ fontSize: 22 }}>{icon}</span>
        <span style={{ fontSize: 14, fontWeight: 700, color, letterSpacing: "0.04em" }}>{name}</span>
      </div>
      {/* Dynamic content */}
      {children}
      {/* Floor glow */}
      <div style={{
        position: "absolute", left: "50%", bottom: 100, transform: "translateX(-50%)",
        width: 80, height: 24, borderRadius: "50%",
        background: `radial-gradient(ellipse, ${color}20, transparent 70%)`,
        filter: "blur(6px)",
      }} />
    </div>
  );
}

function useSkillLogs(logs: NarrativeLog[]): string[] {
  return useMemo(() => {
    const skills: string[] = [];
    for (let i = logs.length - 1; i >= 0 && skills.length < 4; i--) {
      const t = logs[i].text;
      if (t && /skill|SKILL/i.test(t)) {
        const name = t.length > 30 ? t.slice(0, 30) + "…" : t;
        if (!skills.includes(name)) skills.push(name);
      }
    }
    return skills;
  }, [logs]);
}

function PlanRoom({ color, agent, logs }: { color: string; agent?: AgentProjection; logs: NarrativeLog[] }) {
  const summary = agent?.taskSummary;
  const isPlanning = agent?.state === "INCOMING" || agent?.state === "ACK";
  const skillLogs = useSkillLogs(logs);

  return (
    <>
      {/* Whiteboard - shows current task */}
      <div style={{
        position: "absolute", left: 20, top: 55, width: 280, height: 100, borderRadius: 10,
        background: "linear-gradient(180deg, rgba(255,255,255,.07), rgba(255,255,255,.02))",
        border: "1px solid rgba(255,255,255,.1)", boxShadow: "0 4px 12px rgba(0,0,0,.15)",
        overflow: "hidden",
      }}>
        <div style={{
          padding: "8px 10px", fontSize: 11, color: "rgba(255,255,255,.5)", lineHeight: 1.7,
        }}>
          {summary ? (
            <span style={{ color: `${color}cc` }}>{summary.slice(0, 80)}{summary.length > 80 ? "…" : ""}</span>
          ) : (
            <span style={{ opacity: .4 }}>等待新任务...</span>
          )}
        </div>
        {isPlanning && (
          <div style={{
            position: "absolute", bottom: 0, left: 0, height: 2, width: "60%",
            background: `linear-gradient(90deg, ${color}, transparent)`,
            animation: "lo-pulse 1.5s ease-in-out infinite",
          }} />
        )}
      </div>
      {/* Skill loading indicator */}
      {skillLogs.length > 0 && (
        <div style={{
          position: "absolute", left: 20, top: 165, width: 280, height: 60, borderRadius: 8,
          background: "rgba(255,255,255,.02)", border: "1px solid rgba(255,255,255,.05)",
          overflow: "hidden",
        }}>
          <div style={{ padding: "4px 10px", fontSize: 9, color: "rgba(255,255,255,.3)", fontWeight: 600, borderBottom: "1px solid rgba(255,255,255,.04)" }}>
            📚 技能查阅
          </div>
          <div style={{ padding: "3px 10px", display: "flex", flexDirection: "column", gap: 1 }}>
            {skillLogs.slice(0, 3).map((s, i) => (
              <div key={i} style={{ fontSize: 9, color: i === 0 ? `${color}99` : "rgba(255,255,255,.25)", fontFamily: "monospace", lineHeight: 1.3 }}>
                {s}
              </div>
            ))}
          </div>
        </div>
      )}
      <Plant left={270} top={skillLogs.length > 0 ? 240 : 170} />
    </>
  );
}

function ExecuteRoom({ color, agent, logs }: { color: string; agent?: AgentProjection; logs: NarrativeLog[] }) {
  const isWorking = agent?.state === "WORKING" || agent?.state === "BLOCKED";
  const activity = useRecentActivity(logs);

  return (
    <>
      {/* Monitor - shows recent activity */}
      <div style={{
        position: "absolute", left: 20, top: 55, width: 280, height: 130, borderRadius: 10,
        background: isWorking
          ? `linear-gradient(180deg, ${color}12, ${color}04)`
          : "linear-gradient(180deg, rgba(255,255,255,.05), rgba(255,255,255,.02))",
        border: `1px solid ${isWorking ? color + "30" : "rgba(255,255,255,.08)"}`,
        boxShadow: isWorking ? `0 0 24px ${color}15` : "none",
        transition: "all 0.5s ease",
        overflow: "hidden",
      }}>
        {/* Screen scanlines */}
        <div style={{
          position: "absolute", inset: 0, opacity: .03,
          background: "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,.5) 2px, rgba(255,255,255,.5) 3px)",
        }} />
        <div style={{ padding: "8px 10px", display: "flex", flexDirection: "column", gap: 4 }}>
          {activity.length > 0 ? activity.map((a, i) => (
            <div key={i} style={{
              fontSize: 10, color: i === 0 ? `${color}cc` : "rgba(255,255,255,.35)",
              fontFamily: "monospace", lineHeight: 1.4,
              display: "flex", gap: 6,
            }}>
              <span style={{ color: `${color}66`, flexShrink: 0 }}>{i === 0 ? "▸" : " "}</span>
              <span>{a}</span>
            </div>
          )) : (
            <div style={{ fontSize: 10, color: "rgba(255,255,255,.25)", fontFamily: "monospace" }}>
              $ waiting for input_
            </div>
          )}
        </div>
        {/* Cursor blink */}
        {isWorking && (
          <div style={{
            position: "absolute", bottom: 8, left: 18, width: 6, height: 12,
            background: color, borderRadius: 1,
            animation: "lo-blink 1s step-end infinite",
          }} />
        )}
      </div>
    </>
  );
}

function ToolRoom({ color, agent, logs }: { color: string; agent?: AgentProjection; logs: NarrativeLog[] }) {
  const currentTool = agent?.tool;
  const isTooling = agent?.state === "TOOL_CALL" || agent?.state === "COLLABORATING";
  const toolHistory = useToolHistory(logs);

  return (
    <>
      {/* Active tool display */}
      <div style={{
        position: "absolute", left: 20, top: 55, width: 280, height: 60, borderRadius: 10,
        background: isTooling
          ? `linear-gradient(135deg, ${color}20, ${color}08)`
          : "linear-gradient(180deg, rgba(255,255,255,.05), rgba(255,255,255,.02))",
        border: `1px solid ${isTooling ? color + "40" : "rgba(255,255,255,.08)"}`,
        boxShadow: isTooling ? `0 0 30px ${color}20, inset 0 0 20px ${color}08` : "none",
        transition: "all 0.4s ease",
        display: "flex", alignItems: "center", justifyContent: "center", gap: 10,
      }}>
        {currentTool ? (
          <>
            <span style={{ fontSize: 20 }}>⚡</span>
            <span style={{
              fontSize: 13, fontWeight: 700, color,
              fontFamily: "monospace",
              textShadow: `0 0 12px ${color}40`,
            }}>
              {currentTool.length > 24 ? currentTool.slice(0, 24) + "…" : currentTool}
            </span>
          </>
        ) : (
          <span style={{ fontSize: 11, color: "rgba(255,255,255,.25)" }}>待命中</span>
        )}
      </div>

      {/* Tool history */}
      <div style={{
        position: "absolute", left: 20, top: 125, width: 280, height: 80, borderRadius: 8,
        background: "rgba(255,255,255,.02)", border: "1px solid rgba(255,255,255,.05)",
        overflow: "hidden",
      }}>
        <div style={{ padding: "6px 10px", fontSize: 9, color: "rgba(255,255,255,.3)", fontWeight: 600, borderBottom: "1px solid rgba(255,255,255,.04)" }}>
          最近调用
        </div>
        <div style={{ padding: "4px 10px", display: "flex", flexDirection: "column", gap: 2 }}>
          {toolHistory.length > 0 ? toolHistory.map((t, i) => (
            <div key={i} style={{
              fontSize: 10, color: i === 0 ? `${color}99` : "rgba(255,255,255,.25)",
              fontFamily: "monospace", lineHeight: 1.3,
            }}>
              {t}
            </div>
          )) : (
            <div style={{ fontSize: 10, color: "rgba(255,255,255,.2)" }}>暂无记录</div>
          )}
        </div>
      </div>
      <Plant left={270} top={220} />
    </>
  );
}

function DeliverRoom({ color, agent, logs }: { color: string; agent?: AgentProjection; logs: NarrativeLog[] }) {
  const isDone = agent?.state === "DONE";
  const doneCount = useMemo(() => {
    return logs.filter(l => l.kind === "RETURN").length;
  }, [logs]);

  return (
    <>
      {/* Delivery status */}
      <div style={{
        position: "absolute", left: 20, top: 55, width: 280, height: 70, borderRadius: 10,
        background: isDone
          ? `linear-gradient(135deg, ${color}18, ${color}06)`
          : "linear-gradient(180deg, rgba(255,255,255,.05), rgba(255,255,255,.02))",
        border: `1px solid ${isDone ? color + "35" : "rgba(255,255,255,.08)"}`,
        boxShadow: isDone ? `0 0 24px ${color}15` : "none",
        transition: "all 0.5s ease",
        display: "flex", alignItems: "center", justifyContent: "center", gap: 12,
      }}>
        {isDone ? (
          <>
            <span style={{ fontSize: 26 }}>✅</span>
            <span style={{ fontSize: 14, fontWeight: 700, color }}>任务完成</span>
          </>
        ) : (
          <span style={{ fontSize: 11, color: "rgba(255,255,255,.25)" }}>等待交付</span>
        )}
      </div>

      {/* Stats */}
      <div style={{
        position: "absolute", left: 20, top: 140, display: "flex", gap: 12,
      }}>
        <div style={{
          width: 80, height: 50, borderRadius: 8,
          background: "rgba(255,255,255,.03)", border: "1px solid rgba(255,255,255,.06)",
          display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
        }}>
          <span style={{ fontSize: 18, fontWeight: 700, color }}>{doneCount}</span>
          <span style={{ fontSize: 9, color: "rgba(255,255,255,.3)" }}>已完成</span>
        </div>
        <div style={{
          width: 80, height: 50, borderRadius: 8,
          background: "rgba(255,255,255,.03)", border: "1px solid rgba(255,255,255,.06)",
          display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
        }}>
          <span style={{ fontSize: 18, fontWeight: 700, color: "#34d399" }}>
            {logs.filter(l => l.kind === "CALL_TOOL").length}
          </span>
          <span style={{ fontSize: 9, color: "rgba(255,255,255,.3)" }}>工具调用</span>
        </div>
      </div>
      {/* Trophy - only visible after completions */}
      {doneCount > 0 && (
        <div style={{ position: "absolute", right: 30, top: 70, fontSize: 28, opacity: .4 }}>🏆</div>
      )}
      <Plant left={270} top={210} />
    </>
  );
}

function Plant({ left, top }: { left: number; top: number }) {
  return (
    <div style={{ position: "absolute", left, top, width: 22, height: 30, transform: "translateZ(8px)" }}>
      <div style={{
        position: "absolute", left: 4, bottom: 0, width: 14, height: 12, borderRadius: "3px 3px 6px 6px",
        background: "rgba(180,120,70,.25)", border: "1px solid rgba(180,120,70,.15)",
      }} />
      <div style={{
        position: "absolute", left: 2, top: 0, width: 18, height: 18, borderRadius: "50%",
        background: "radial-gradient(circle, rgba(52,211,153,.3), rgba(22,163,74,.12))",
      }} />
    </div>
  );
}

export function StaffZone() {
  const agent = useAgent();
  const logs = useLogs();

  return (
    <>
      {Object.entries(WORK_ZONES).map(([key, zone]) => (
        <RoomWall
          key={key}
          x={zone.room.x}
          y={zone.room.y}
          w={zone.room.w}
          h={zone.room.h}
          color={zone.color}
          label={zone.label}
        >
          {key === "plan" && <PlanRoom color={zone.color} agent={agent} logs={logs} />}
          {key === "execute" && <ExecuteRoom color={zone.color} agent={agent} logs={logs} />}
          {key === "tool" && <ToolRoom color={zone.color} agent={agent} logs={logs} />}
          {key === "deliver" && <DeliverRoom color={zone.color} agent={agent} logs={logs} />}
        </RoomWall>
      ))}

      {/* Corridor */}
      <div style={{
        position: "absolute",
        left: 30, top: 285, width: 1410, height: 18, borderRadius: 9,
        background: "linear-gradient(90deg, rgba(92,200,255,.06), rgba(167,139,250,.06))",
        border: "1px solid rgba(255,255,255,.04)",
        transform: "translateZ(2px)",
        pointerEvents: "none",
      }} />
    </>
  );
}
