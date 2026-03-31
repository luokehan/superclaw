import type { AgentEventPayload } from "@/gateway/types";
import type { PerceptionEngine } from "@/perception/perception-engine";
import { useProjectionStore } from "@/perception/projection-store";

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

let runCounter = 0;
function nextRunId(): string {
  return `demo-${Date.now()}-${++runCounter}`;
}

function makeEvent(
  overrides: Partial<AgentEventPayload> & Pick<AgentEventPayload, "stream" | "data" | "sessionKey">,
): AgentEventPayload {
  return {
    runId: overrides.runId ?? nextRunId(),
    seq: overrides.seq ?? 1,
    stream: overrides.stream,
    ts: overrides.ts ?? Date.now(),
    data: overrides.data,
    sessionKey: overrides.sessionKey,
  };
}

/**
 * 1. 客户消息到达 → GM 接单 → Sales 分析 → 写入记忆墙
 */
export async function triggerUserTask(engine: PerceptionEngine): Promise<void> {
  const runId = nextRunId();

  // Gateway 接收外部消息
  engine.ingest(
    makeEvent({
      runId,
      stream: "lifecycle",
      data: { phase: "start", trigger: "external", agentId: "main" },
      sessionKey: "telegram:main:main",
    }),
  );
  await wait(850);

  // GM 分发给 Sales
  engine.ingest(
    makeEvent({
      runId,
      seq: 2,
      stream: "lifecycle",
      data: { phase: "start", agentId: "main" },
      sessionKey: "agent:main:main",
    }),
  );
  await wait(600);

  // Sales 开始工作
  const salesRunId = nextRunId();
  engine.ingest(
    makeEvent({
      runId: salesRunId,
      stream: "lifecycle",
      data: { phase: "start", agentId: "ai-researcher" },
      sessionKey: "agent:ai-researcher:task",
    }),
  );
  await wait(800);

  // Sales 调用工具
  engine.ingest(
    makeEvent({
      runId: salesRunId,
      seq: 2,
      stream: "tool",
      data: { phase: "start", name: "web_search" },
      sessionKey: "agent:ai-researcher:task",
    }),
  );
  await wait(1500);

  // Sales 回复结果
  engine.ingest(
    makeEvent({
      runId: salesRunId,
      seq: 3,
      stream: "assistant",
      data: { text: "已完成客户需求分析，发现 3 个潜在商机。报告已写入记忆墙。" },
      sessionKey: "agent:ai-researcher:task",
    }),
  );
  await wait(600);

  // 写入记忆墙——更新 ProjectionStore
  useProjectionStore.getState().applyPerceivedEvent({
    id: `mem-${Date.now()}`,
    startTs: Date.now(),
    endTs: Date.now(),
    kind: "RETURN",
    level: 2,
    actors: ["ai-researcher"],
    area: "memory",
    summary: "客户需求分析完成，写入记忆墙",
    displayPriority: 5,
    holdMs: 1500,
    debugRefs: [],
  });

  // 结束
  engine.ingest(
    makeEvent({
      runId: salesRunId,
      seq: 4,
      stream: "lifecycle",
      data: { phase: "end", agentId: "ai-researcher" },
      sessionKey: "agent:ai-researcher:task",
    }),
  );
  engine.ingest(
    makeEvent({
      runId,
      seq: 3,
      stream: "lifecycle",
      data: { phase: "end", agentId: "main" },
      sessionKey: "agent:main:main",
    }),
  );
}

/**
 * 2. GM 拉起协作 → sub-agent 出现 → 协作完成
 */
export async function triggerCollab(engine: PerceptionEngine): Promise<void> {
  const runId = nextRunId();

  // GM 开始
  engine.ingest(
    makeEvent({
      runId,
      stream: "lifecycle",
      data: { phase: "start", agentId: "main" },
      sessionKey: "agent:main:collab",
    }),
  );
  await wait(900);

  // 拉起 sub-agent
  const subRunId = nextRunId();
  engine.ingest(
    makeEvent({
      runId: subRunId,
      stream: "lifecycle",
      data: { phase: "start", agentId: "coder", isSubAgent: true, parentAgentId: "main" },
      sessionKey: "agent:coder:collab",
    }),
  );
  await wait(1500);

  // sub-agent 工作
  engine.ingest(
    makeEvent({
      runId: subRunId,
      seq: 2,
      stream: "tool",
      data: { phase: "start", name: "code_exec" },
      sessionKey: "agent:coder:collab",
    }),
  );
  await wait(1200);

  // sub-agent 回复
  engine.ingest(
    makeEvent({
      runId: subRunId,
      seq: 3,
      stream: "assistant",
      data: { text: "代码审查完成，发现 2 个优化建议。" },
      sessionKey: "agent:coder:collab",
    }),
  );
  await wait(800);

  // 协作结束
  engine.ingest(
    makeEvent({
      runId: subRunId,
      seq: 4,
      stream: "lifecycle",
      data: { phase: "end", agentId: "coder" },
      sessionKey: "agent:coder:collab",
    }),
  );
  engine.ingest(
    makeEvent({
      runId,
      seq: 2,
      stream: "lifecycle",
      data: { phase: "end", agentId: "main" },
      sessionKey: "agent:main:collab",
    }),
  );
}

/**
 * 3. Cron 广播 → Finance 处理 → 完成
 */
export async function triggerCron(engine: PerceptionEngine): Promise<void> {
  const runId = nextRunId();

  // Cron 触发
  engine.ingest(
    makeEvent({
      runId,
      stream: "lifecycle",
      data: { phase: "start", trigger: "cron", agentId: "ecommerce" },
      sessionKey: "agent:ecommerce:cron",
    }),
  );
  await wait(1200);

  // Finance 处理
  engine.ingest(
    makeEvent({
      runId,
      seq: 2,
      stream: "tool",
      data: { phase: "start", name: "analyze_data" },
      sessionKey: "agent:ecommerce:cron",
    }),
  );
  await wait(1200);

  // 完成
  engine.ingest(
    makeEvent({
      runId,
      seq: 3,
      stream: "assistant",
      data: { text: "定时报表已生成，财务数据汇总完成。" },
      sessionKey: "agent:ecommerce:cron",
    }),
  );
  await wait(600);

  engine.ingest(
    makeEvent({
      runId,
      seq: 4,
      stream: "lifecycle",
      data: { phase: "end", agentId: "ecommerce" },
      sessionKey: "agent:ecommerce:cron",
    }),
  );
}

/**
 * 4. Heartbeat 巡检 → 工位依次脉冲
 */
export async function triggerHeartbeat(engine: PerceptionEngine): Promise<void> {
  const agents = ["main", "ai-researcher", "coder", "ecommerce"];

  for (const agentId of agents) {
    const runId = nextRunId();
    engine.ingest(
      makeEvent({
        runId,
        stream: "lifecycle",
        data: { phase: "thinking", agentId },
        sessionKey: `agent:${agentId}:heartbeat`,
      }),
    );
    await wait(260);
    engine.ingest(
      makeEvent({
        runId,
        seq: 2,
        stream: "lifecycle",
        data: { phase: "end", agentId },
        sessionKey: `agent:${agentId}:heartbeat`,
      }),
    );
    await wait(260);
  }
}

/**
 * 5. Ops 阻塞 → 保留 4.2s → IT 排查 → 恢复
 */
export async function triggerIncident(engine: PerceptionEngine): Promise<void> {
  const runId = nextRunId();

  // Ops 发生阻塞
  engine.ingest(
    makeEvent({
      runId,
      stream: "lifecycle",
      data: { phase: "start", agentId: "coder" },
      sessionKey: "agent:coder:ops",
    }),
  );
  await wait(800);

  engine.ingest(
    makeEvent({
      runId,
      seq: 2,
      stream: "error",
      data: { message: "API 连接超时，服务暂时不可用" },
      sessionKey: "agent:coder:ops",
    }),
  );
  await wait(4200);

  // IT 介入排查
  const itRunId = nextRunId();
  engine.ingest(
    makeEvent({
      runId: itRunId,
      stream: "lifecycle",
      data: { phase: "start", agentId: "ecommerce" },
      sessionKey: "agent:ecommerce:fix",
    }),
  );
  await wait(1300);

  // 恢复——先发 lifecycle start（触发 RECOVER）
  engine.ingest(
    makeEvent({
      runId: itRunId,
      seq: 2,
      stream: "lifecycle",
      data: { phase: "start", agentId: "coder" },
      sessionKey: "agent:coder:ops",
    }),
  );
  engine.ingest(
    makeEvent({
      runId: itRunId,
      seq: 3,
      stream: "assistant",
      data: { text: "服务已恢复正常，重新建立连接成功。" },
      sessionKey: "agent:ecommerce:fix",
    }),
  );
  await wait(600);

  engine.ingest(
    makeEvent({
      runId: itRunId,
      seq: 4,
      stream: "lifecycle",
      data: { phase: "end", agentId: "ecommerce" },
      sessionKey: "agent:ecommerce:fix",
    }),
  );
  engine.ingest(
    makeEvent({
      runId,
      seq: 3,
      stream: "lifecycle",
      data: { phase: "end", agentId: "coder" },
      sessionKey: "agent:coder:ops",
    }),
  );
}

/**
 * Demo scenarios with colored button configs.
 * `labelKey` is the i18n key under `office:livingOffice.demo.*`.
 */
export const DEMO_BUTTONS = [
  { labelKey: "userTask", fn: triggerUserTask, color: "rgba(59,130,246,0.8)", hoverColor: "rgba(59,130,246,1)" },
  { labelKey: "collab", fn: triggerCollab, color: "rgba(139,92,246,0.8)", hoverColor: "rgba(139,92,246,1)" },
  { labelKey: "cron", fn: triggerCron, color: "rgba(245,158,11,0.8)", hoverColor: "rgba(245,158,11,1)" },
  { labelKey: "heartbeat", fn: triggerHeartbeat, color: "rgba(59,130,246,0.8)", hoverColor: "rgba(59,130,246,1)" },
  { labelKey: "incident", fn: triggerIncident, color: "rgba(239,68,68,0.8)", hoverColor: "rgba(239,68,68,1)" },
] as const;

/**
 * 自动播放模式——12 秒间隔循环执行 4 个主要演示
 */
export function startAutoPlay(engine: PerceptionEngine): () => void {
  const sequence = [triggerUserTask, triggerHeartbeat, triggerCollab, triggerCron];
  let index = 0;
  let running = true;
  let timerId: ReturnType<typeof setTimeout> | null = null;

  async function playNext(): Promise<void> {
    if (!running) return;
    const fn = sequence[index % sequence.length];
    index++;
    await fn(engine);
    if (running) {
      timerId = setTimeout(() => void playNext(), 12_000);
    }
  }

  timerId = setTimeout(() => void playNext(), 3_000);

  return () => {
    running = false;
    if (timerId) clearTimeout(timerId);
  };
}
