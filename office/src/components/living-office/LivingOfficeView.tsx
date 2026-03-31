import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { isMockMode } from "@/gateway/adapter-provider";
import { useProjectionStore } from "@/perception/projection-store";
import type { AgentProjection } from "@/perception/types";
import { useOfficeStore } from "@/store/office-store";
import { useCronStore } from "@/store/console-stores/cron-store";
import { AgentCharacter2D5 } from "./characters/AgentCharacter2D5";
import { useSubtitle } from "./characters/useWorkPhase";
import { DESK_CONFIGS, CANVAS_W, CANVAS_H, WORK_ZONES } from "./config";
import { EventLogPanel } from "./hud/EventLogPanel";
import { GatewayStatus } from "./hud/GatewayStatus";
import { HudBar } from "./hud/HudBar";
import { startAutoPlay } from "./hud/MockDemoDriver";
import { usePerceptionEngine } from "./hud/perception-context";
import { StatsPanel } from "./hud/StatsPanel";
import { OfficeStage } from "./scene/OfficeStage";
import { Desk } from "./workspace/Desk";
import { CronZone } from "./zones/CronZone";
import { GatewayZone } from "./zones/GatewayZone";
import { OpsZone } from "./zones/OpsZone";
import { StaffZone } from "./zones/StaffZone";

function agentStateToDeskStatus(state: string): "idle" | "busy" | "blocked" | "heartbeat" {
  switch (state) {
    case "WORKING":
    case "TOOL_CALL":
    case "COLLABORATING":
    case "INCOMING":
    case "ACK":
      return "busy";
    case "BLOCKED":
      return "blocked";
    default:
      return "idle";
  }
}

function useStageScale(containerRef: React.RefObject<HTMLDivElement | null>): string {
  const [scale, setScale] = useState("0.92");

  const updateScale = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;
    const { width, height } = el.getBoundingClientRect();
    const sx = width / CANVAS_W;
    const sy = height / CANVAS_H;
    const s = Math.min(sx, sy);
    setScale(s.toFixed(3));
  }, [containerRef]);

  useEffect(() => {
    updateScale();
    const ro = new ResizeObserver(updateScale);
    if (containerRef.current) ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, [updateScale, containerRef]);

  return scale;
}

function stateToZoneKey(state: string): keyof typeof WORK_ZONES {
  switch (state) {
    case "INCOMING":
    case "ACK":
      return "plan";
    case "WORKING":
    case "BLOCKED":
      return "execute";
    case "TOOL_CALL":
    case "COLLABORATING":
      return "tool";
    case "DONE":
      return "deliver";
    default:
      return "plan";
  }
}

function SuperClawCharacter({ agent }: { agent: AgentProjection | undefined }) {
  const desk = DESK_CONFIGS[0];
  const state = agent?.state ?? "IDLE";
  const zoneKey = stateToZoneKey(state);
  const zone = WORK_ZONES[zoneKey];
  const subtitle = useSubtitle(state, agent?.tool, agent?.taskSummary);

  return (
    <>
      <AgentCharacter2D5
        agentId={agent?.agentId ?? desk.id}
        deskId={desk.id}
        name="🦞 SuperClaw"
        perceivedState={state}
        toolName={agent?.tool}
      />

      {/* Floating subtitle bubble — follows zone position */}
      <div
        style={{
          position: "absolute",
          left: zone.left - 100,
          top: zone.top - 80,
          width: 240,
          textAlign: "center",
          transform: "translateZ(30px)",
          transition: "left 0.9s cubic-bezier(.25,.9,.2,1), top 0.9s cubic-bezier(.25,.9,.2,1)",
          pointerEvents: "none",
          zIndex: 200,
        }}
      >
        <div
          style={{
            display: "inline-block",
            padding: "6px 14px",
            borderRadius: 14,
            background: "rgba(9,15,28,.88)",
            border: `1px solid ${zone.color}44`,
            boxShadow: `0 4px 16px rgba(0,0,0,.3), 0 0 12px ${zone.color}22`,
            fontSize: 14,
            fontWeight: 600,
            color: zone.color,
            whiteSpace: "nowrap",
          }}
        >
          {subtitle}
        </div>
      </div>
    </>
  );
}

export function LivingOfficeView() {
  const navigate = useNavigate();
  const agents = useProjectionStore((s) => s.agents);
  const connectionStatus = useOfficeStore((s) => s.connectionStatus);
  const engine = usePerceptionEngine();
  const autoPlayCleanup = useRef<(() => void) | null>(null);
  const stageContainerRef = useRef<HTMLDivElement>(null);
  const stageScale = useStageScale(stageContainerRef);

  const superClaw = useMemo(() => {
    return agents.values().next().value as AgentProjection | undefined;
  }, [agents]);

  const desk = DESK_CONFIGS[0];

  useEffect(() => {
    if (!isMockMode() || !engine) return;
    autoPlayCleanup.current = startAutoPlay(engine);
    return () => {
      autoPlayCleanup.current?.();
      autoPlayCleanup.current = null;
    };
  }, [engine]);

  useEffect(() => {
    if (!isMockMode() && connectionStatus !== "connected") {
      return;
    }

    const cronStore = useCronStore.getState();
    void cronStore.fetchTasks();
    const unsubscribe = cronStore.initEventListeners();
    const timer = setInterval(() => {
      void useCronStore.getState().fetchTasks();
    }, 30_000);

    return () => {
      clearInterval(timer);
      unsubscribe();
    };
  }, [connectionStatus]);

  return (
    <div
      className="living-office"
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        overflow: "hidden",
        background: "var(--lo-app-bg)",
        fontFamily:
          'Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, "PingFang SC", "Microsoft YaHei", sans-serif',
        color: "var(--lo-text)",
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "var(--lo-app-overlay)",
          pointerEvents: "none",
        }}
      />

      <HudBar
        left={<GatewayStatus />}
        center={<EventLogPanel />}
        right={<StatsPanel />}
      />

      {/* 3D toggle button */}
      <button
        onClick={() => {
          useOfficeStore.getState().setViewMode("3d");
          navigate("/office");
        }}
        style={{
          position: "absolute",
          bottom: 16,
          right: 16,
          zIndex: 30,
          display: "flex",
          alignItems: "center",
          gap: 6,
          padding: "8px 14px",
          borderRadius: 12,
          border: "1px solid rgba(255,255,255,.12)",
          background: "rgba(15,23,42,.85)",
          backdropFilter: "blur(8px)",
          color: "rgba(255,255,255,.7)",
          fontSize: 12,
          fontWeight: 600,
          cursor: "pointer",
          transition: "all 0.2s",
          boxShadow: "0 4px 12px rgba(0,0,0,.3)",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = "rgba(15,23,42,.95)";
          e.currentTarget.style.borderColor = "rgba(92,200,255,.4)";
          e.currentTarget.style.color = "rgba(255,255,255,.95)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = "rgba(15,23,42,.85)";
          e.currentTarget.style.borderColor = "rgba(255,255,255,.12)";
          e.currentTarget.style.color = "rgba(255,255,255,.7)";
        }}
      >
        <span style={{ fontSize: 16 }}>🧊</span>
        3D 视图
      </button>

      <div
        ref={stageContainerRef}
        style={{
          position: "absolute",
          inset: "46px 8px 6px 8px",
          "--lo-stage-scale": stageScale,
          "--lo-stage-scale-sm": stageScale,
        } as React.CSSProperties}
      >
        <OfficeStage>
          <GatewayZone />
          <OpsZone />
          <CronZone />
          <StaffZone />

          {/* Desk in plan room */}
          <Desk
            key={desk.id}
            config={desk}
            status={superClaw ? agentStateToDeskStatus(superClaw.state) : "idle"}
            bubble=""
          />

          <SuperClawCharacter agent={superClaw} />
        </OfficeStage>
      </div>
    </div>
  );
}
