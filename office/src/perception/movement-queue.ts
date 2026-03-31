import type { PerceivedKind } from "./types";

// --- 并发移动控制 ---
// 同时最多 MAX_CONCURRENT 个 Agent 移动，超出排队等待

const MAX_CONCURRENT = 2;

interface QueuedMove {
  agentId: string;
  targetArea: string;
  eventKind: PerceivedKind;
  resolve: () => void;
}

let activeCount = 0;
const queue: QueuedMove[] = [];

// 仅允许这 5 种事件触发跨区移动
const MOVE_ALLOWED_KINDS = new Set<PerceivedKind>([
  "DISPATCH",
  "COLLAB",
  "SPAWN_SUBAGENT",
  "RETURN",
  "BLOCK",
]);

export function canTriggerMove(eventKind: PerceivedKind): boolean {
  return MOVE_ALLOWED_KINDS.has(eventKind);
}

export function requestMove(
  agentId: string,
  targetArea: string,
  eventKind: PerceivedKind,
): Promise<void> {
  if (!canTriggerMove(eventKind)) {
    return Promise.resolve();
  }

  return new Promise<void>((resolve) => {
    const item: QueuedMove = { agentId, targetArea, eventKind, resolve };

    if (activeCount < MAX_CONCURRENT) {
      startMove(item);
    } else {
      queue.push(item);
    }
  });
}

function startMove(item: QueuedMove): void {
  activeCount++;
  item.resolve();
}

export function completeMove(): void {
  activeCount = Math.max(0, activeCount - 1);

  if (queue.length > 0 && activeCount < MAX_CONCURRENT) {
    const next = queue.shift();
    if (next) {
      startMove(next);
    }
  }
}

export function getActiveCount(): number {
  return activeCount;
}

export function getQueueLength(): number {
  return queue.length;
}

export function resetMovementQueue(): void {
  activeCount = 0;
  queue.length = 0;
}
