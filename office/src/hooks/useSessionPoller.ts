import { useEffect, useRef, type RefObject } from "react";
import type { GatewayRpcClient } from "@/gateway/rpc-client";
import { useProjectionStore } from "@/perception/projection-store";
import type { PerceivedEvent } from "@/perception/types";
import { EventLevel } from "@/perception/types";
import { generateNarrative } from "@/perception/narrative-generator";

const POLL_INTERVAL_MS = 1500;
const MAX_HISTORY_LIMIT = 50;
/** After activity stops, wait before DONE. */
const COOLDOWN_MS = 4000;
/** Stay at DONE before resetting to IDLE. */
const DONE_LINGER_MS = 5000;

let idCounter = 0;

interface SessionEntry { key: string; updatedAt?: number }
interface SessionsListResponse { sessions?: SessionEntry[] }
interface AgentInfo { id: string; activeRuns?: number; pendingRuns?: number; queuedRuns?: number }
interface AgentsListResponse { agents?: AgentInfo[] }
interface ChatHistoryMessage {
  role: string;
  content: Array<{ type: string; name?: string; text?: string }>;
  timestamp?: number;
}
interface ChatHistoryResponse { messages?: ChatHistoryMessage[] }

/**
 * Polls chat.history to detect tool calls and drive character animation.
 *
 * Detection strategy:
 * - First poll: snapshot all existing tool keys (baseline). Everything is "old".
 * - Subsequent polls: any NEW tool key not in baseline = live activity.
 *   This works regardless of timestamps or activeRuns timing.
 *
 * Animation flow:
 * - New tool detected → CALL_TOOL → character walks to tool room
 * - New messages (no tools) → DISPATCH → character walks to execute room
 * - No new data for COOLDOWN_MS → RETURN → character walks to delivery
 * - After DONE_LINGER_MS → reset to IDLE → character walks to plan room
 */
export function useSessionPoller(rpcRef: RefObject<GatewayRpcClient | null>) {
  const baselineToolKeysRef = useRef<Set<string> | null>(null);
  const seenLiveToolKeysRef = useRef<Set<string>>(new Set());
  const cachedSessionKeyRef = useRef<string | null>(null);
  const lastLiveActivityAtRef = useRef(0);
  const returnEmittedRef = useRef(false);
  const prevMessageCountRef = useRef(-1);

  useEffect(() => {
    if (!rpcRef.current) return;

    const poll = async () => {
      const rpc = rpcRef.current;
      if (!rpc) return;

      try {
        const agents = useProjectionStore.getState().agents;
        const agentId = agents.keys().next().value as string | undefined;
        if (!agentId) return;

        // Quick idle check from gateway
        let gatewayIdle = true;
        try {
          const resp = await rpc.request<AgentsListResponse>("agents.list", {});
          const list = resp?.agents;
          if (Array.isArray(list)) {
            const info = list.find((a) => a.id === agentId);
            gatewayIdle = (info?.activeRuns ?? 0) === 0 &&
                          (info?.pendingRuns ?? 0) === 0 &&
                          (info?.queuedRuns ?? 0) === 0;
          }
        } catch { /* ignore */ }

        // Get session key
        let sessionKey = cachedSessionKeyRef.current;
        try {
          const resp = await rpc.request<SessionsListResponse>("sessions.list", {});
          const sessions = resp?.sessions;
          if (Array.isArray(sessions) && sessions.length > 0) {
            sessionKey = sessions[0].key;
            cachedSessionKeyRef.current = sessionKey;
          }
        } catch { /* use cached */ }
        if (!sessionKey) return;

        // Get chat history
        const histResp = await rpc.request<ChatHistoryResponse>("chat.history", {
          sessionKey,
          limit: MAX_HISTORY_LIMIT,
        });
        if (!histResp?.messages) return;

        const messages = histResp.messages;
        const messageCount = messages.length;
        const now = Date.now();
        const applyEvent = useProjectionStore.getState().applyPerceivedEvent;

        // Collect ALL tool keys from current history
        const allToolKeys = new Map<string, { name: string; ts: number }>();
        for (const msg of messages) {
          if (msg.role !== "assistant" || !Array.isArray(msg.content)) continue;
          for (const block of msg.content) {
            if (block.type !== "toolCall" && block.type !== "tool_use") continue;
            const toolName = block.name ?? "unknown";
            const ts = msg.timestamp ?? 0;
            const toolKey = `${toolName}:${ts}`;
            allToolKeys.set(toolKey, { name: toolName, ts });
          }
        }

        // First poll: establish baseline
        if (baselineToolKeysRef.current === null) {
          baselineToolKeysRef.current = new Set(allToolKeys.keys());
          prevMessageCountRef.current = messageCount;
          // Add all to narrative logs as history
          for (const [, tool] of allToolKeys) {
            addToolToNarrativeOnly(agentId, tool);
          }
          return;
        }

        // Find NEW tools (not in baseline AND not already seen as live)
        const newLiveTools: Array<{ name: string; ts: number }> = [];
        for (const [key, tool] of allToolKeys) {
          if (baselineToolKeysRef.current.has(key)) continue;
          if (seenLiveToolKeysRef.current.has(key)) continue;
          seenLiveToolKeysRef.current.add(key);
          newLiveTools.push(tool);
        }

        const hasNewMessages = messageCount !== prevMessageCountRef.current;
        prevMessageCountRef.current = messageCount;

        // New tool calls → character to tool room
        if (newLiveTools.length > 0) {
          lastLiveActivityAtRef.current = now;
          returnEmittedRef.current = false;
          for (const tool of newLiveTools) {
            applyEvent(makeToolEvent(agentId, tool));
            addToolToNarrativeOnly(agentId, tool);
          }
          setTaskSummary(agentId, messages);
          return;
        }

        // New messages without tools and gateway says active → thinking
        if (hasNewMessages && !gatewayIdle) {
          lastLiveActivityAtRef.current = now;
          returnEmittedRef.current = false;
          const agent = useProjectionStore.getState().agents.get(agentId);
          if (agent && agent.state === "IDLE") {
            applyEvent({
              id: `poll-work-${now}-${++idCounter}`,
              startTs: now, endTs: now,
              kind: "DISPATCH", level: EventLevel.L2,
              actors: [agentId], area: "staff",
              summary: "处理中...", displayPriority: 2, holdMs: 1500, debugRefs: [],
            });
          }
          setTaskSummary(agentId, messages);
          return;
        }

        // No new data — handle cooldown transitions
        if (lastLiveActivityAtRef.current === 0) return;

        const agent = useProjectionStore.getState().agents.get(agentId);
        if (!agent || agent.state === "IDLE") return;

        const elapsed = now - lastLiveActivityAtRef.current;
        const effectiveCooldown = gatewayIdle ? Math.min(COOLDOWN_MS, 3000) : COOLDOWN_MS;

        if (elapsed >= effectiveCooldown && !returnEmittedRef.current) {
          // → DONE (交付台)
          returnEmittedRef.current = true;
          const event: PerceivedEvent = {
            id: `poll-done-${now}-${++idCounter}`,
            startTs: now, endTs: now,
            kind: "RETURN", level: EventLevel.L2,
            actors: [agentId], area: "staff",
            summary: "", displayPriority: 2, holdMs: 2000, debugRefs: [],
          };
          event.summary = generateNarrative(event);
          applyEvent(event);
        } else if (returnEmittedRef.current && elapsed >= effectiveCooldown + DONE_LINGER_MS) {
          // → IDLE (规划室)
          if (agent.taskSummary) {
            useProjectionStore.setState((s) => {
              const a = s.agents.get(agentId);
              if (a) a.taskSummary = undefined;
            });
          }
          useProjectionStore.getState().resetAgent(agentId);
          lastLiveActivityAtRef.current = 0;
          returnEmittedRef.current = false;
        }
      } catch { /* RPC not available */ }
    };

    const timer = setInterval(poll, POLL_INTERVAL_MS);
    poll();
    return () => clearInterval(timer);
  }, [rpcRef]);
}

function makeToolEvent(agentId: string, tool: { name: string; ts: number }): PerceivedEvent {
  const event: PerceivedEvent = {
    id: `poll-${Date.now()}-${++idCounter}`,
    startTs: tool.ts, endTs: tool.ts,
    kind: "CALL_TOOL", level: EventLevel.L3,
    actors: [agentId], area: "staff",
    summary: "", displayPriority: 3, holdMs: 2000, debugRefs: [],
    toolName: tool.name,
  };
  event.summary = generateNarrative(event);
  return event;
}

function addToolToNarrativeOnly(agentId: string, tool: { name: string; ts: number }): void {
  const event = makeToolEvent(agentId, tool);
  useProjectionStore.setState((state) => {
    state.narrativeLogs.push({
      ts: event.startTs, text: event.summary, level: event.level, kind: event.kind,
    });
    if (state.narrativeLogs.length > 50) {
      state.narrativeLogs.splice(0, state.narrativeLogs.length - 50);
    }
  });
}

function setTaskSummary(agentId: string, messages: ChatHistoryMessage[]): void {
  const last = [...messages].reverse().find((m) => m.role === "assistant" && Array.isArray(m.content));
  if (!last) return;
  for (const block of last.content) {
    if (block.type === "text" && block.text && block.text.length > 10) {
      const agent = useProjectionStore.getState().agents.get(agentId);
      if (agent && !agent.taskSummary) {
        useProjectionStore.setState((s) => {
          const a = s.agents.get(agentId);
          if (a) a.taskSummary = block.text!.slice(0, 100);
        });
      }
      break;
    }
  }
}
