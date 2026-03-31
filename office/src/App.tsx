import { lazy, Suspense, useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Routes, Route, Navigate, useLocation, useNavigate } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { ConsoleLayout } from "@/components/layout/ConsoleLayout";
import { LivingOfficeView } from "@/components/living-office/LivingOfficeView";
import { FloorPlan } from "@/components/office-2d/FloorPlan";
import { AgentsPage } from "@/components/pages/AgentsPage";
import { ChannelsPage } from "@/components/pages/ChannelsPage";
import { CronPage } from "@/components/pages/CronPage";
import { DashboardPage } from "@/components/pages/DashboardPage";
import { SettingsPage } from "@/components/pages/SettingsPage";
import { SkillsPage } from "@/components/pages/SkillsPage";
import type { PageId } from "@/gateway/types";
import { useGatewayConnection } from "@/hooks/useGatewayConnection";
import { useResponsive } from "@/hooks/useResponsive";
import { useProjectionToOfficeSync } from "@/hooks/useProjectionToOfficeSync";
import { useOfficeStore } from "@/store/office-store";
import { PerceptionEngineContext } from "@/components/living-office/hud/perception-context";

const Scene3D = lazy(() => import("@/components/office-3d/Scene3D"));

function Scene3DFallback() {
  const { t } = useTranslation("office");
  return (
    <div className="flex h-full w-full items-center justify-center bg-gray-50 dark:bg-gray-950">
      <div className="flex flex-col items-center gap-3">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
        <span className="text-sm text-gray-500 dark:text-gray-400">{t("loading3D")}</span>
      </div>
    </div>
  );
}

function BackToLivingOfficeButton() {
  const location = useLocation();
  const navigate = useNavigate();
  if (location.pathname !== "/office") return null;
  return (
    <button
      onClick={() => navigate("/")}
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
      <span style={{ fontSize: 16 }}>🦞</span>
      返回 2D
    </button>
  );
}

function OfficeView() {
  const viewMode = useOfficeStore((s) => s.viewMode);
  const [fading, setFading] = useState(false);
  const [displayMode, setDisplayMode] = useState(viewMode);

  useEffect(() => {
    if (viewMode !== displayMode) {
      setFading(true);
      const timer = setTimeout(() => {
        setDisplayMode(viewMode);
        setFading(false);
      }, 150);
      return () => clearTimeout(timer);
    }
  }, [viewMode, displayMode]);

  return (
    <div
      className="h-full w-full transition-opacity duration-300"
      style={{ opacity: fading ? 0 : 1, position: "relative" }}
    >
      {displayMode === "2d" ? (
        <FloorPlan />
      ) : (
        <Suspense fallback={<Scene3DFallback />}>
          <Scene3D />
        </Suspense>
      )}
      <BackToLivingOfficeButton />
    </div>
  );
}

function ThemeSync() {
  const theme = useOfficeStore((s) => s.theme);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [theme]);

  return null;
}

const PAGE_MAP: Record<string, PageId> = {
  "/": "office",
  "/office": "office",
  "/living-office": "office",
  "/dashboard": "dashboard",
  "/agents": "agents",
  "/channels": "channels",
  "/skills": "skills",
  "/cron": "cron",
  "/settings": "settings",
};

function resolveGatewayWsUrl(pathOrUrl: string, fallbackUrl: string): string {
  const value = (pathOrUrl || "").trim();
  if (value.startsWith("ws://") || value.startsWith("wss://")) {
    return value;
  }
  if (value.startsWith("http://") || value.startsWith("https://")) {
    const url = new URL(value);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    return url.toString();
  }
  if (value.startsWith("/")) {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}${value}`;
  }
  return fallbackUrl;
}

function PageTracker() {
  const location = useLocation();
  const setCurrentPage = useOfficeStore((s) => s.setCurrentPage);

  useEffect(() => {
    const page = PAGE_MAP[location.pathname] ?? "office";
    setCurrentPage(page);
  }, [location.pathname, setCurrentPage]);

  return null;
}

export function App() {
  const injected = (window as unknown as Record<string, unknown>).__OPENCLAW_CONFIG__ as
    | { gatewayUrl?: string; gatewayToken?: string; gatewayWsPath?: string }
    | undefined;
  const configuredGatewayUrl = injected?.gatewayUrl || import.meta.env.VITE_GATEWAY_URL || "ws://localhost:18789";
  const gatewayUrl = resolveGatewayWsUrl(
    injected?.gatewayWsPath || import.meta.env.VITE_GATEWAY_WS_PATH || "/gateway-ws",
    configuredGatewayUrl,
  );
  const gatewayToken = injected?.gatewayToken || import.meta.env.VITE_GATEWAY_TOKEN || "";
  const { isMobile } = useResponsive();
  const setViewMode = useOfficeStore((s) => s.setViewMode);

  const { wsClient, perceptionEngine } = useGatewayConnection({ url: gatewayUrl, token: gatewayToken });

  // Sync projection-store (fed by session poller) into office-store for 3D/2D views
  useProjectionToOfficeSync();

  useEffect(() => {
    if (isMobile) {
      setViewMode("2d");
    }
  }, [isMobile, setViewMode]);

  return (
    <PerceptionEngineContext value={perceptionEngine}>
      <ThemeSync />
      <PageTracker />
      <Routes>
        <Route element={<AppShell wsClient={wsClient} isMobile={isMobile} />}>
          <Route path="/" element={<LivingOfficeView />} />
          <Route path="/office" element={<OfficeView />} />
          <Route path="/living-office" element={<LivingOfficeView />} />
        </Route>
        <Route element={<ConsoleLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/agents" element={<AgentsPage />} />
          <Route path="/channels" element={<ChannelsPage />} />
          <Route path="/skills" element={<SkillsPage />} />
          <Route path="/cron" element={<CronPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </PerceptionEngineContext>
  );
}
