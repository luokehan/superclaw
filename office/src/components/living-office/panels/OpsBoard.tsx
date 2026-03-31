import { useProjectionStore } from "@/perception/projection-store";
import { useOfficeStore } from "@/store/office-store";
import { GlassPanel } from "./GlassPanel";
import { PanelHead } from "./PanelHead";

export function OpsBoard() {
  const agents = useOfficeStore((s) => s.agents);
  const metrics = useOfficeStore((s) => s.globalMetrics);
  const opsEvents = useProjectionStore((s) => s.sceneArea.opsRules);

  const superClaw = Array.from(agents.values()).find((a) => !a.isPlaceholder);
  const status = superClaw?.status ?? "offline";
  const currentTool = superClaw?.currentTool?.name ?? "无";

  const liveRules =
    opsEvents.length > 0
      ? opsEvents.slice(-4).reverse().map((entry) => `${entry.tag} · ${entry.text}`)
      : [
        `状态 · ${status === "idle" ? "✅ 待命" : status === "thinking" ? "🧠 思考中" : status === "tool_calling" ? "⚡ 工具调用" : status === "speaking" ? "💬 回复中" : status === "error" ? "❌ 错误" : "⚪ " + status}`,
        `当前工具 · ${currentTool}`,
        `Token 消耗 · ${metrics.totalTokens.toLocaleString()}`,
        `Token 速率 · ${metrics.tokenRate.toFixed(0)}/min`,
      ];

  return (
    <GlassPanel
      style={{
        position: "absolute",
        left: 508,
        top: 38,
        width: 504,
        height: 214,
        transform: "translateZ(16px)",
      }}
    >
      <PanelHead title="SuperClaw 运行面板" subtitle="实时状态监控" />
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 7,
          padding: "0 14px 14px",
        }}
      >
        {liveRules.slice(0, 4).map((rule) => (
          <div
            key={rule}
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
            <span style={{ color: "#e6eefc" }}>{rule}</span>
            <span style={{ color: "var(--lo-muted)" }}>实时</span>
          </div>
        ))}
      </div>
    </GlassPanel>
  );
}
