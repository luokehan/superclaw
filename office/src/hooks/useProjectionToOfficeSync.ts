import { useEffect, useRef } from "react";
import { useProjectionStore } from "@/perception/projection-store";
import { useOfficeStore } from "@/store/office-store";
import type { PerceivedAgentState } from "@/perception/types";
import type { AgentVisualStatus, AgentZone } from "@/gateway/types";

const PERCEIVED_TO_VISUAL: Record<PerceivedAgentState, AgentVisualStatus> = {
  IDLE: "idle",
  INCOMING: "thinking",
  ACK: "thinking",
  WORKING: "thinking",
  TOOL_CALL: "tool_calling",
  WAITING: "idle",
  COLLABORATING: "tool_calling",
  RETURNING: "idle",
  DONE: "idle",
  BLOCKED: "error",
  RECOVERED: "idle",
};

// Map 2D perceived state → 3D zone
// desk=规划室, hotDesk=执行间, meeting=工具房, lounge=交付台
const PERCEIVED_TO_ZONE: Record<PerceivedAgentState, AgentZone> = {
  IDLE: "desk",
  INCOMING: "desk",
  ACK: "desk",
  WORKING: "hotDesk",
  TOOL_CALL: "meeting",
  WAITING: "desk",
  COLLABORATING: "meeting",
  RETURNING: "lounge",
  DONE: "lounge",
  BLOCKED: "hotDesk",
  RECOVERED: "desk",
};

/**
 * Syncs projection-store state (fed by useSessionPoller) into office-store
 * so the 3D scene and 2D FloorPlan can also display tool call status
 * and agent movement between zones.
 */
export function useProjectionToOfficeSync(): void {
  const projectionAgents = useProjectionStore((s) => s.agents);
  const narrativeLogs = useProjectionStore((s) => s.narrativeLogs);
  const lastZoneRef = useRef<Map<string, AgentZone>>(new Map());

  useEffect(() => {
    const store = useOfficeStore.getState();
    const officeAgents = store.agents;

    for (const [, projection] of projectionAgents) {
      const visualStatus = PERCEIVED_TO_VISUAL[projection.state] ?? "idle";
      const targetZone = PERCEIVED_TO_ZONE[projection.state] ?? "desk";

      // Find matching office agent
      let officeAgent = officeAgents.get(projection.agentId);
      if (!officeAgent) {
        for (const [id, agent] of officeAgents) {
          if (agent.name === projection.agentId || agent.name === projection.role || id === projection.role) {
            officeAgent = agent;
            break;
          }
        }
      }

      if (!officeAgent) continue;

      const toolName = projection.tool ?? null;
      const currentTool = toolName ? { name: toolName, startedAt: Date.now() } : null;

      // Update status and tool
      if (officeAgent.status !== visualStatus || officeAgent.currentTool?.name !== toolName) {
        store.updateAgent(officeAgent.id, {
          status: visualStatus,
          currentTool,
        });
      }

      // Trigger movement if zone changed
      const prevZone = lastZoneRef.current.get(officeAgent.id) ?? officeAgent.zone;
      if (targetZone !== prevZone) {
        lastZoneRef.current.set(officeAgent.id, targetZone);
        store.startMovement(officeAgent.id, targetZone);
      }
    }

    // Sync tool call history from narrative logs
    const toolLogs = narrativeLogs
      .filter((l) => l.kind === "CALL_TOOL")
      .slice(-10)
      .map((l) => ({ name: l.text, timestamp: l.ts }));

    if (toolLogs.length > 0) {
      for (const [, officeAgent] of officeAgents) {
        if (officeAgent.isSubAgent || officeAgent.isPlaceholder) continue;
        const existingCount = officeAgent.toolCallHistory?.length ?? 0;
        if (toolLogs.length > existingCount) {
          store.updateAgent(officeAgent.id, {
            toolCallHistory: toolLogs,
            toolCallCount: toolLogs.length,
          });
        }
        break;
      }
    }
  }, [projectionAgents, narrativeLogs]);
}
