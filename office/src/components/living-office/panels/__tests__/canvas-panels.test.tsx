import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import i18n from "@/i18n";
import { useProjectionStore } from "@/perception/projection-store";
import { useOfficeStore } from "@/store/office-store";
import { useCronStore } from "@/store/console-stores/cron-store";
import { CronBoard } from "../CronBoard";
import { GatewayCore } from "../GatewayCore";
import { MemoryWall } from "../MemoryWall";
import { OpsBoard } from "../OpsBoard";
import { ProjectRoom } from "../ProjectRoom";

const t = (key: string) => i18n.t(`office:${key}`);

describe("Living office canvas panels", () => {
  beforeEach(() => {
    useProjectionStore.setState({
      narrativeLogs: [],
      sceneArea: {
        gatewayStream: [
          { label: "WebSocket", detail: "实时事件中", active: true },
          { label: "Event Bus", detail: "客户消息到达", active: true },
          { label: "RPC", detail: "actors 2", active: true },
          { label: "Health", detail: "正常", active: true },
        ],
        cronTasks: [],
        memoryItems: [],
        projectTasks: [],
        opsRules: [],
      },
    });
    useOfficeStore.setState({
      connectionStatus: "connected",
      operatorScopes: ["operator.admin"],
      globalMetrics: {
        activeAgents: 2,
        totalAgents: 4,
        totalTokens: 0,
        tokenRate: 0,
        collaborationHeat: 0,
      },
      agents: new Map(),
      links: [],
      maxSubAgents: 8,
      agentToAgentConfig: { enabled: true, allow: ["main"] },
      lastSessionsSnapshot: null,
    });
    useCronStore.setState({ tasks: [] });
  });

  it("MemoryWall renders live memory items", () => {
    useProjectionStore.setState({
      sceneArea: {
        ...useProjectionStore.getState().sceneArea,
        memoryItems: [{ text: "真实事件摘要", tag: "gateway" }],
      },
    });

    render(
      <div className="living-office">
        <MemoryWall />
      </div>,
    );

    expect(screen.getByText("真实事件摘要")).toBeInTheDocument();
    expect(screen.getByText("gateway")).toBeInTheDocument();
  });

  it("MemoryWall shows empty state instead of mock entries when there is no live data", () => {
    render(
      <div className="living-office">
        <MemoryWall />
      </div>,
    );

    expect(screen.getByText(t("livingOffice.panels.memoryEmpty"))).toBeInTheDocument();
  });

  it("ProjectRoom renders live sub-agent sessions", () => {
    useOfficeStore.setState({
      lastSessionsSnapshot: {
        fetchedAt: Date.now(),
        sessions: [{
          sessionKey: "agent:main:subagent:123",
          agentId: "sub-1",
          label: "Research SubAgent",
          task: "整理需求",
          requesterSessionKey: "agent:main:main",
          startedAt: Date.now(),
        }],
      },
    });

    render(
      <div className="living-office">
        <ProjectRoom />
      </div>,
    );

    expect(screen.getByText("Research SubAgent")).toBeInTheDocument();
    expect(screen.getByText("整理需求")).toBeInTheDocument();
  });

  it("ProjectRoom falls back safely when there is no session snapshot", () => {
    render(
      <div className="living-office">
        <ProjectRoom />
      </div>,
    );

    expect(screen.getByText(t("livingOffice.panels.projectEmpty"))).toBeInTheDocument();
  });

  it("OpsBoard renders live operational metrics when no incident log exists", () => {
    render(
      <div className="living-office">
        <OpsBoard />
      </div>,
    );

    expect(screen.getByText(`${t("livingOffice.panels.opsAgentToAgent")} · ${t("livingOffice.panels.opsEnabled")}`)).toBeInTheDocument();
    expect(screen.getByText(`${t("livingOffice.panels.opsSubCapacity")} · 0/8`)).toBeInTheDocument();
  });

  it("GatewayCore renders live gateway stream details", () => {
    render(
      <div className="living-office">
        <GatewayCore />
      </div>,
    );

    expect(screen.getByText("实时事件中")).toBeInTheDocument();
    expect(screen.getByText("客户消息到达")).toBeInTheDocument();
    expect(screen.getByText("actors 2")).toBeInTheDocument();
  });

  it("CronBoard renders live cron store tasks", () => {
    useCronStore.setState({
      tasks: [{
        id: "cron-1",
        name: "同步日报",
        schedule: { kind: "cron", expr: "0 9 * * *" },
        enabled: true,
        createdAtMs: Date.now(),
        updatedAtMs: Date.now(),
        sessionTarget: "main",
        wakeMode: "now",
        payload: { kind: "systemEvent", text: "sync" },
        state: { runningAtMs: Date.now() },
      }],
    });

    render(
      <div className="living-office">
        <CronBoard />
      </div>,
    );

    expect(screen.getByText("同步日报")).toBeInTheDocument();
    expect(screen.getByText("running")).toBeInTheDocument();
  });
});
