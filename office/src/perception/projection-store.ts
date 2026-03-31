import { enableMapSet } from "immer";
import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import i18n from "@/i18n";

enableMapSet();

import {
  MAX_NARRATIVE_LOGS,
  type AgentProjection,
  type NarrativeLog,
  type PerceivedAgentState,
  type PerceivedEvent,
  type SceneAreaState,
} from "./types";

// --- Kind → State 映射 ---

const KIND_TO_STATE: Record<string, PerceivedAgentState> = {
  ARRIVE: "INCOMING",
  DISPATCH: "WORKING",
  ACK: "ACK",
  FOCUS: "WORKING",
  CALL_TOOL: "TOOL_CALL",
  WAIT: "WAITING",
  SPAWN_SUBAGENT: "COLLABORATING",
  COLLAB: "COLLABORATING",
  RETURN: "DONE",
  BROADCAST_CRON: "IDLE",
  POLL_HEARTBEAT: "IDLE",
  BLOCK: "BLOCKED",
  RECOVER: "RECOVERED",
};

// --- Store 类型 ---

interface ProjectionStoreState {
  agents: Map<string, AgentProjection>;
  narrativeLogs: NarrativeLog[];
  sceneArea: SceneAreaState;

  initAgent: (agentId: string, role: string, deskId: string) => void;
  initAgentsBatch: (agents: Array<{ agentId: string; role: string; deskId: string }>) => void;
  applyPerceivedEvent: (event: PerceivedEvent) => void;
  resetAgent: (agentId: string) => void;
  getSnapshot: () => {
    agents: Map<string, AgentProjection>;
    narrativeLogs: NarrativeLog[];
    sceneArea: SceneAreaState;
  };
}

const SCENE_AREA_LIMIT = 5;

function createDefaultSceneArea(): SceneAreaState {
  return {
    gatewayStream: [
      { label: "WebSocket", detail: i18n.t("office:livingOffice.gateway.connecting"), active: false },
      { label: "Event Bus", detail: i18n.t("office:livingOffice.gateway.ready"), active: false },
      { label: "RPC", detail: i18n.t("office:livingOffice.gateway.ready"), active: false },
      { label: "Health", detail: i18n.t("office:livingOffice.gateway.normal"), active: true },
    ],
    cronTasks: [],
    memoryItems: [],
    projectTasks: [],
    opsRules: [],
  };
}

function pushUniqueLimited<T>(
  list: T[],
  item: T,
  isSame: (left: T, right: T) => boolean,
  limit = SCENE_AREA_LIMIT,
): void {
  const existingIndex = list.findIndex((entry) => isSame(entry, item));
  if (existingIndex >= 0) {
    list.splice(existingIndex, 1);
  }
  list.push(item);
  if (list.length > limit) {
    list.splice(0, list.length - limit);
  }
}

function summarizeActors(event: PerceivedEvent): string {
  if (event.actors.length === 0) {
    return "system";
  }
  if (event.actors.length === 1) {
    return event.actors[0];
  }
  return `${event.actors[0]} +${event.actors.length - 1}`;
}

function deriveMemoryTag(event: PerceivedEvent): string {
  switch (event.kind) {
    case "BROADCAST_CRON":
      return "cron";
    case "BLOCK":
      return "incident";
    case "RECOVER":
      return "recovery";
    case "CALL_TOOL":
      return "tool";
    case "SPAWN_SUBAGENT":
      return "project";
    default:
      return event.area;
  }
}

function syncSceneAreaFromEvent(sceneArea: SceneAreaState, event: PerceivedEvent): void {
  if (event.summary && event.kind !== "POLL_HEARTBEAT") {
    pushUniqueLimited(
      sceneArea.memoryItems,
      { text: event.summary, tag: deriveMemoryTag(event) },
      (left, right) => left.text === right.text,
    );
  }

  if (event.kind === "SPAWN_SUBAGENT" || event.kind === "COLLAB") {
    pushUniqueLimited(
      sceneArea.projectTasks,
      {
        title: event.summary,
        subtitle: `active · ${summarizeActors(event)}`,
      },
      (left, right) => left.title === right.title,
    );
  }

  if (event.kind === "BLOCK" || event.kind === "RECOVER") {
    pushUniqueLimited(
      sceneArea.opsRules,
      {
        text: event.summary,
        tag: event.kind === "BLOCK" ? "incident" : "recovery",
      },
      (left, right) => left.text === right.text,
    );
  }

  if (event.kind === "BROADCAST_CRON") {
    pushUniqueLimited(
      sceneArea.cronTasks,
      {
        time: new Date(event.startTs).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }),
        name: event.summary,
        status: "running",
      },
      (left, right) => left.name === right.name && left.time === right.time,
    );
  }

  if (event.kind === "ARRIVE" || event.kind === "DISPATCH") {
    const webSocketLine = sceneArea.gatewayStream.find((line) => line.label === "WebSocket");
    if (webSocketLine) {
      webSocketLine.detail = i18n.t("office:livingOffice.gateway.streaming");
      webSocketLine.active = true;
    }

    const streamLine = sceneArea.gatewayStream.find((line) => line.label === "Event Bus");
    if (streamLine) {
      streamLine.detail = event.summary.slice(0, 30);
      streamLine.active = true;
    }

    const rpcLine = sceneArea.gatewayStream.find((line) => line.label === "RPC");
    if (rpcLine) {
      rpcLine.detail = `actors ${event.actors.length || 1}`;
      rpcLine.active = true;
    }
  }

  if (event.kind === "BLOCK" || event.kind === "RECOVER") {
    const healthLine = sceneArea.gatewayStream.find((line) => line.label === "Health");
    if (healthLine) {
      healthLine.detail = event.kind === "BLOCK"
        ? i18n.t("office:livingOffice.gateway.alert")
        : i18n.t("office:livingOffice.gateway.recovered");
      healthLine.active = event.kind !== "BLOCK";
    }
  }
}

// --- localStorage persistence for narrativeLogs ---
const LOGS_STORAGE_KEY = "oc_narrativeLogs";
const AGENT_STORAGE_KEY = "oc_agentSnapshot";

function loadPersistedLogs(): NarrativeLog[] {
  try {
    const raw = localStorage.getItem(LOGS_STORAGE_KEY);
    if (raw) return JSON.parse(raw) as NarrativeLog[];
  } catch { /* ignore */ }
  return [];
}

function persistLogs(logs: NarrativeLog[]): void {
  try {
    localStorage.setItem(LOGS_STORAGE_KEY, JSON.stringify(logs.slice(-MAX_NARRATIVE_LOGS)));
  } catch { /* quota exceeded */ }
}

function loadPersistedAgent(): Partial<AgentProjection> | null {
  try {
    const raw = localStorage.getItem(AGENT_STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch { /* ignore */ }
  return null;
}

function persistAgent(agent: AgentProjection): void {
  try {
    localStorage.setItem(AGENT_STORAGE_KEY, JSON.stringify({
      agentId: agent.agentId,
      role: agent.role,
      state: agent.state,
      tool: agent.tool,
      taskSummary: agent.taskSummary,
      deskId: agent.deskId,
    }));
  } catch { /* ignore */ }
}

export const useProjectionStore = create<ProjectionStoreState>()(
  immer((set, get) => ({
    agents: new Map<string, AgentProjection>(),
    narrativeLogs: loadPersistedLogs(),
    sceneArea: createDefaultSceneArea(),

    initAgent: (agentId: string, role: string, deskId: string) => {
      set((state) => {
        state.agents.set(agentId, {
          agentId,
          role,
          state: "IDLE",
          deskId,
          load: 0,
          lastHeartbeatAt: Date.now(),
          health: "ok",
        });
      });
    },

    initAgentsBatch: (agents) => {
      set((state) => {
        const persisted = loadPersistedAgent();
        for (const { agentId, role, deskId } of agents) {
          const restored = persisted && persisted.agentId === agentId ? persisted : null;
          state.agents.set(agentId, {
            agentId,
            role: restored?.role ?? role,
            state: (restored?.state as PerceivedAgentState) ?? "IDLE",
            tool: restored?.tool,
            taskSummary: restored?.taskSummary,
            deskId,
            load: 0,
            lastHeartbeatAt: Date.now(),
            health: "ok",
          });
        }
      });
    },

    applyPerceivedEvent: (event: PerceivedEvent) => {
      set((state) => {
        // 更新涉及的 Agent 投影状态
        const newState = KIND_TO_STATE[event.kind] ?? "IDLE";

        for (const actorId of event.actors) {
          let agent = state.agents.get(actorId);
          if (!agent) {
            // Auto-create agent on first event (supports real Gateway agents)
            agent = {
              agentId: actorId,
              role: actorId,
              state: "IDLE",
              deskId: actorId,
              load: 0,
              lastHeartbeatAt: Date.now(),
              health: "ok",
            };
            state.agents.set(actorId, agent);
          }

          agent.state = newState;

          if (event.kind === "CALL_TOOL") {
            agent.tool = event.toolName ?? event.summary;
          } else {
            agent.tool = undefined;
          }

          if (event.kind === "BLOCK") {
            agent.health = "error";
          } else if (event.kind === "RECOVER") {
            agent.health = "ok";
          }

          if (event.taskText) {
            agent.taskSummary = event.taskText;
          } else if (event.summary) {
            agent.taskSummary = event.summary;
          }

          // Clear taskSummary when agent goes idle
          if (agent.state === "IDLE") {
            agent.taskSummary = undefined;
          }
        }

        // 追加叙事日志
        if (event.summary && event.kind !== "POLL_HEARTBEAT") {
          state.narrativeLogs.push({
            ts: event.startTs,
            text: event.summary,
            level: event.level,
            kind: event.kind,
          });
          if (state.narrativeLogs.length > MAX_NARRATIVE_LOGS) {
            state.narrativeLogs.splice(0, state.narrativeLogs.length - MAX_NARRATIVE_LOGS);
          }
          // Persist to localStorage
          queueMicrotask(() => persistLogs(get().narrativeLogs));
        }

        // Persist agent snapshot
        for (const actorId of event.actors) {
          const a = state.agents.get(actorId);
          if (a) queueMicrotask(() => persistAgent(a));
        }

        syncSceneAreaFromEvent(state.sceneArea, event);
      });
    },

    resetAgent: (agentId: string) => {
      set((state) => {
        const agent = state.agents.get(agentId);
        if (!agent) return;
        agent.state = "IDLE";
        agent.tool = undefined;
        agent.taskSummary = undefined;
        agent.sessionId = undefined;
      });
    },

    getSnapshot: () => {
      const state = get();
      return {
        agents: new Map(state.agents),
        narrativeLogs: [...state.narrativeLogs],
        sceneArea: { ...state.sceneArea },
      };
    },
  })),
);
