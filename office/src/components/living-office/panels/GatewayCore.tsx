import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import i18n from "@/i18n";
import { useProjectionStore } from "@/perception/projection-store";
import { useOfficeStore } from "@/store/office-store";

export function GatewayCore() {
  const { t } = useTranslation("office");
  const [clock, setClock] = useState(() => formatTime());
  const connectionStatus = useOfficeStore((s) => s.connectionStatus);
  const operatorScopes = useOfficeStore((s) => s.operatorScopes);
  const globalMetrics = useOfficeStore((s) => s.globalMetrics);
  const gatewayStream = useProjectionStore((s) => s.sceneArea.gatewayStream);

  useEffect(() => {
    const id = setInterval(() => setClock(formatTime()), 1000);
    return () => clearInterval(id);
  }, []);

  const busLines = [
    {
      title: t("livingOffice.panels.busWebSocket"),
      detail:
        gatewayStream.find((line) => line.label === "WebSocket")?.detail ??
        connectionStatus,
    },
    {
      title: t("livingOffice.panels.busEventSpine"),
      detail:
        gatewayStream.find((line) => line.label === "Event Bus")?.detail ??
        `active ${globalMetrics.activeAgents}/${globalMetrics.totalAgents}`,
    },
    {
      title: t("livingOffice.panels.busRpcScope"),
      detail:
        gatewayStream.find((line) => line.label === "RPC")?.detail ??
        (operatorScopes[0] ?? "operator"),
    },
  ];

  return (
    <div
      style={{
        position: "absolute",
        left: 48,
        top: 38,
        width: 404,
        height: 214,
        transform: "translateZ(20px)",
        borderRadius: 24,
        background:
          "linear-gradient(180deg, rgba(12, 30, 55, .96), rgba(8,16,30,.96))",
        border: "1px solid rgba(92,200,255,.24)",
        boxShadow:
          "0 18px 40px rgba(0,0,0,.28), 0 0 35px rgba(92,200,255,.12), inset 0 1px 0 rgba(255,255,255,.08)",
        overflow: "hidden",
      }}
    >
      {/* Scan wave */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(90deg, transparent, rgba(92,200,255,.18), transparent)",
          transform: "translateX(-100%)",
          animation: "lo-scan 6s linear infinite",
        }}
      />

      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          padding: "14px 16px 6px",
          position: "relative",
        }}
      >
        <b style={{ fontSize: 21, color: "#e9f2ff" }}>{t("livingOffice.panels.gatewayHeader")}</b>
        <span style={{ fontSize: 16, color: "var(--lo-muted)" }}>{clock}</span>
      </div>

      {/* Bus lines */}
      <div
        style={{
          position: "absolute",
          left: 16,
          right: 16,
          bottom: 14,
          height: 64,
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 10,
        }}
      >
        {busLines.map((bus) => (
          <div
            key={bus.title}
            style={{
              borderRadius: 14,
              background: "rgba(255,255,255,.04)",
              border: "1px solid rgba(255,255,255,.05)",
              padding: 10,
              fontSize: 16,
            }}
          >
            <b style={{ display: "block", marginBottom: 3, color: "#e9f2ff" }}>
              {bus.title}
            </b>
            <small style={{ color: "var(--lo-muted)" }}>{bus.detail}</small>
          </div>
        ))}
      </div>
    </div>
  );
}

function formatTime(): string {
  const locale = i18n.language === "zh" ? "zh-CN" : "en-US";
  return new Date().toLocaleTimeString(locale, { hour12: false });
}
