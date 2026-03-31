import type { PerceivedAgentState, PerceivedKind } from "./types";

// --- 视觉指令 ---

export interface VisualInstructions {
  cssClass: string;
  shouldMove: boolean;
  moveTarget?: string;
  holdMs: number;
}

// --- 状态转换结果 ---

export interface TransitionResult {
  nextState: PerceivedAgentState;
  visual: VisualInstructions;
}

// --- 合法转换矩阵 ---

const TRANSITIONS: Record<PerceivedAgentState, Set<PerceivedAgentState>> = {
  IDLE: new Set(["INCOMING"]),
  INCOMING: new Set(["ACK"]),
  ACK: new Set(["WORKING"]),
  WORKING: new Set(["TOOL_CALL", "WAITING", "COLLABORATING", "DONE", "BLOCKED"]),
  TOOL_CALL: new Set(["WORKING", "WAITING", "DONE", "BLOCKED"]),
  WAITING: new Set(["WORKING", "DONE", "BLOCKED"]),
  COLLABORATING: new Set(["RETURNING", "BLOCKED"]),
  RETURNING: new Set(["DONE"]),
  DONE: new Set(["IDLE"]),
  BLOCKED: new Set(["RECOVERED"]),
  RECOVERED: new Set(["WORKING", "IDLE"]),
};

// --- 感知事件 → 目标状态映射 ---

const EVENT_TO_STATE: Partial<Record<PerceivedKind, PerceivedAgentState>> = {
  ARRIVE: "INCOMING",
  DISPATCH: "WORKING",
  ACK: "ACK",
  FOCUS: "WORKING",
  CALL_TOOL: "TOOL_CALL",
  WAIT: "WAITING",
  SPAWN_SUBAGENT: "COLLABORATING",
  COLLAB: "COLLABORATING",
  RETURN: "RETURNING",
  BROADCAST_CRON: "IDLE",
  POLL_HEARTBEAT: "IDLE",
  BLOCK: "BLOCKED",
  RECOVER: "RECOVERED",
};

// --- 每种状态的视觉规则 ---

const STATE_VISUALS: Record<PerceivedAgentState, Omit<VisualInstructions, "moveTarget">> = {
  IDLE: { cssClass: "idle", shouldMove: false, holdMs: 0 },
  INCOMING: { cssClass: "incoming", shouldMove: false, holdMs: 1000 },
  ACK: { cssClass: "ack", shouldMove: false, holdMs: 1200 },
  WORKING: { cssClass: "working", shouldMove: false, holdMs: 2500 },
  TOOL_CALL: { cssClass: "tool-call", shouldMove: false, holdMs: 2000 },
  WAITING: { cssClass: "waiting", shouldMove: false, holdMs: 2500 },
  COLLABORATING: { cssClass: "collaborating", shouldMove: true, holdMs: 5000 },
  RETURNING: { cssClass: "returning", shouldMove: true, holdMs: 1500 },
  DONE: { cssClass: "done", shouldMove: false, holdMs: 1200 },
  BLOCKED: { cssClass: "blocked", shouldMove: false, holdMs: 5000 },
  RECOVERED: { cssClass: "recovered", shouldMove: false, holdMs: 2500 },
};

// --- 移动触发事件白名单 ---

const MOVE_TRIGGER_KINDS = new Set<PerceivedKind>([
  "DISPATCH",
  "COLLAB",
  "SPAWN_SUBAGENT",
  "RETURN",
  "BLOCK",
]);

// --- 同状态晋升映射 ---
// 当事件映射到当前已处于的状态时，自动晋升到下一个合法状态

const SAME_STATE_PROMOTIONS: Partial<Record<PerceivedAgentState, PerceivedAgentState>> = {
  RETURNING: "DONE",
};

// --- 主要转换函数（纯函数） ---

export function transition(
  currentState: PerceivedAgentState,
  eventKind: PerceivedKind,
): TransitionResult {
  const targetState = EVENT_TO_STATE[eventKind];

  // 无映射的事件种类：保持当前状态
  if (!targetState) {
    return {
      nextState: currentState,
      visual: { ...STATE_VISUALS[currentState] },
    };
  }

  // IDLE 跳转永远合法（逃生路径）
  if (targetState === "IDLE") {
    return {
      nextState: "IDLE",
      visual: { ...STATE_VISUALS.IDLE },
    };
  }

  // 同状态：检查是否有合法的"晋升"目标
  // 例如 RETURNING + RETURN → DONE（RETURN 事件默认映射到 RETURNING，但已在 RETURNING 则晋升到 DONE）
  if (currentState === targetState) {
    const promotions = SAME_STATE_PROMOTIONS[currentState];
    if (promotions) {
      return {
        nextState: promotions,
        visual: {
          ...STATE_VISUALS[promotions],
          shouldMove: STATE_VISUALS[promotions].shouldMove && MOVE_TRIGGER_KINDS.has(eventKind),
        },
      };
    }
    return {
      nextState: currentState,
      visual: { ...STATE_VISUALS[currentState] },
    };
  }

  const allowed = TRANSITIONS[currentState];
  const isLegal = allowed.has(targetState);

  if (!isLegal) {
    // 非法转换：警告日志，但仍接受转换（不崩溃）
    console.warn(
      `[StateMachine] Illegal transition: ${currentState} → ${targetState} (event: ${eventKind}). Accepting with degradation.`,
    );
  }

  const baseVisual = STATE_VISUALS[targetState];
  const shouldMove = baseVisual.shouldMove && MOVE_TRIGGER_KINDS.has(eventKind);

  return {
    nextState: targetState,
    visual: {
      ...baseVisual,
      shouldMove,
    },
  };
}

// --- 快速跳回 IDLE ---

export function resetToIdle(): TransitionResult {
  return {
    nextState: "IDLE",
    visual: { ...STATE_VISUALS.IDLE },
  };
}

// --- 检查转换是否合法（供测试使用） ---

export function isLegalTransition(
  from: PerceivedAgentState,
  to: PerceivedAgentState,
): boolean {
  if (to === "IDLE") return true;
  return TRANSITIONS[from].has(to);
}

// --- 导出常量供测试使用 ---

export { EVENT_TO_STATE, STATE_VISUALS, TRANSITIONS };
