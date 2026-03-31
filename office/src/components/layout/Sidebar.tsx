import { useMemo, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useLocation } from "react-router-dom";
import { AgentDetailPanel } from "@/components/panels/AgentDetailPanel";
import { EventTimeline } from "@/components/panels/EventTimeline";
import { MetricsPanel } from "@/components/panels/MetricsPanel";
import { CollapsibleSection } from "@/components/shared/CollapsibleSection";
import { SvgAvatar } from "@/components/shared/SvgAvatar";
import type { AgentVisualStatus } from "@/gateway/types";
import { useSidebarLayout } from "@/hooks/useSidebarLayout";
import { STATUS_COLORS } from "@/lib/constants";
import { useOfficeStore } from "@/store/office-store";

export function Sidebar() {
  const { t } = useTranslation("layout");
  const agents = useOfficeStore((s) => s.agents);
  const selectedAgentId = useOfficeStore((s) => s.selectedAgentId);
  const selectAgent = useOfficeStore((s) => s.selectAgent);
  const collapsed = useOfficeStore((s) => s.sidebarCollapsed);
  const setSidebarCollapsed = useOfficeStore((s) => s.setSidebarCollapsed);

  const { getSection, toggleSection, setSectionHeight } = useSidebarLayout();

  const superClaw = useMemo(() => {
    const list = Array.from(agents.values()).filter((a) => !a.isPlaceholder);
    return list[0] ?? null;
  }, [agents]);

  useEffect(() => {
    if (superClaw && !selectedAgentId) {
      selectAgent(superClaw.id);
    }
  }, [superClaw, selectedAgentId, selectAgent]);

  if (collapsed) {
    return (
      <aside className="flex w-12 flex-col items-center border-l border-gray-200 bg-white py-3 dark:border-gray-700 dark:bg-gray-900">
        <button
          onClick={() => setSidebarCollapsed(false)}
          className="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
          title={t("sidebar.expand")}
        >
          ◀
        </button>
      </aside>
    );
  }

  const metricsSection = getSection("metrics");
  const detailSection = getSection("detail");
  const timelineSection = getSection("timeline");

  return (
    <aside className="flex w-80 flex-col border-l border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900">
      {/* Sidebar header */}
      <div className="flex h-8 shrink-0 items-center justify-between border-b border-gray-200 px-3 dark:border-gray-700">
        <span className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
          🦞 SuperClaw
        </span>
        <div className="flex items-center gap-2">
          <ViewSwitcher />
          <button
            onClick={() => setSidebarCollapsed(true)}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            title={t("sidebar.collapse")}
          >
            ▶
          </button>
        </div>
      </div>

      {/* SuperClaw status card */}
      {superClaw && (
        <div className="border-b border-gray-100 px-3 py-3 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <SvgAvatar agentId={superClaw.id} size={32} />
            <div className="min-w-0 flex-1">
              <div className="text-sm font-semibold text-gray-800 dark:text-gray-200">
                🦞 SuperClaw
              </div>
              <div className="flex items-center gap-1.5">
                <span
                  className="inline-block h-2 w-2 rounded-full"
                  style={{
                    backgroundColor: STATUS_COLORS[superClaw.status as AgentVisualStatus],
                  }}
                />
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {t(`common:agent.statusLabels.${superClaw.status}`)}
                </span>
                {superClaw.currentTool && (
                  <span className="text-xs text-orange-500">
                    ⚡ {superClaw.currentTool.name}
                  </span>
                )}
              </div>
            </div>
          </div>
          {superClaw.speechBubble?.text && (
            <div className="mt-2 rounded bg-gray-50 px-2 py-1.5 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300">
              {superClaw.speechBubble.text.slice(0, 120)}
              {superClaw.speechBubble.text.length > 120 ? "..." : ""}
            </div>
          )}
        </div>
      )}

      {/* Metrics */}
      <CollapsibleSection
        id="metrics"
        title={t("sidebar.metricsTitle")}
        collapsed={metricsSection.collapsed}
        onToggle={() => toggleSection("metrics")}
        height={metricsSection.height}
        onHeightChange={(h) => setSectionHeight("metrics", h)}
        minHeight={120}
        maxHeight={400}
      >
        <MetricsPanel />
      </CollapsibleSection>

      {/* Agent detail */}
      {selectedAgentId && (
        <CollapsibleSection
          id="detail"
          title="详情"
          collapsed={detailSection.collapsed}
          onToggle={() => toggleSection("detail")}
          height={detailSection.height}
          onHeightChange={(h) => setSectionHeight("detail", h)}
          minHeight={80}
          maxHeight={400}
        >
          <AgentDetailPanel />
        </CollapsibleSection>
      )}

      {/* Event timeline */}
      <CollapsibleSection
        id="timeline"
        title={t("sidebar.eventTimeline")}
        collapsed={timelineSection.collapsed}
        onToggle={() => toggleSection("timeline")}
        height={timelineSection.height}
        onHeightChange={(h) => setSectionHeight("timeline", h)}
        minHeight={150}
        maxHeight={600}
        flex
      >
        <EventTimeline />
      </CollapsibleSection>
    </aside>
  );
}

function ViewSwitcher() {
  const navigate = useNavigate();
  const location = useLocation();
  const isOffice = location.pathname === "/office";
  const isLiving = location.pathname === "/" || location.pathname === "/living-office";

  return (
    <div className="flex gap-1">
      <button
        onClick={() => navigate("/")}
        className={`rounded px-1.5 py-0.5 text-[9px] font-semibold transition-colors ${
          isLiving
            ? "bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300"
            : "text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
        }`}
      >
        Living
      </button>
      <button
        onClick={() => navigate("/office")}
        className={`rounded px-1.5 py-0.5 text-[9px] font-semibold transition-colors ${
          isOffice
            ? "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300"
            : "text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
        }`}
      >
        2D/3D
      </button>
    </div>
  );
}

