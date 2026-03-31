import { describe, expect, it, vi } from "vitest";
import { buildAgentCostsFromSessionsUsage, buildSnapshotFromSessions } from "@/hooks/useUsagePoller";

describe("buildSnapshotFromSessions", () => {
  it("aggregates fresh session totals by agent", () => {
    vi.spyOn(Date, "now").mockReturnValue(123456);

    const snapshot = buildSnapshotFromSessions([
      { key: "agent:main:main", totalTokens: 1200, totalTokensFresh: true },
      { key: "agent:main:subagent:worker-1", totalTokens: 300, totalTokensFresh: true },
      { key: "agent:reviewer:main", totalTokens: 900, totalTokensFresh: true },
      { key: "agent:stale:main", totalTokens: 500, totalTokensFresh: false },
      { key: "channel:telegram:123", totalTokens: 700, totalTokensFresh: true },
    ]);

    expect(snapshot).toEqual({
      timestamp: 123456,
      total: 2400,
      byAgent: {
        main: 1500,
        reviewer: 900,
      },
    });
  });

  it("returns null when there are no usable fresh totals", () => {
    const snapshot = buildSnapshotFromSessions([
      { key: "agent:main:main", totalTokensFresh: false, totalTokens: 1200 },
      { key: "channel:telegram:123", totalTokensFresh: true, totalTokens: 200 },
      { key: "agent:reviewer:main" },
    ]);

    expect(snapshot).toBeNull();
  });
});

describe("buildAgentCostsFromSessionsUsage", () => {
  it("extracts per-agent total cost from sessions.usage aggregates", () => {
    const costs = buildAgentCostsFromSessionsUsage({
      aggregates: {
        byAgent: [
          { agentId: "main", totals: { totalCost: 1.25 } },
          { agentId: "reviewer", totals: { totalCost: 0.4 } },
          { agentId: "zero", totals: { totalCost: 0 } },
        ],
      },
    });

    expect(costs).toEqual({
      main: 1.25,
      reviewer: 0.4,
    });
  });

  it("returns null when sessions.usage has no usable agent costs", () => {
    expect(
      buildAgentCostsFromSessionsUsage({
        aggregates: {
          byAgent: [{ agentId: "main", totals: { totalCost: 0 } }],
        },
      }),
    ).toBeNull();
    expect(buildAgentCostsFromSessionsUsage(null)).toBeNull();
  });
});
