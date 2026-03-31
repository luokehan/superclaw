import { ZONE_CONFIGS } from "../config";
import { GatewayCore } from "../panels/GatewayCore";
import { ZonePanel } from "./ZonePanel";

export function GatewayZone() {
  const cfg = ZONE_CONFIGS.gateway;

  return (
    <>
      <ZonePanel config={cfg} />
      <GatewayCore />
      <Conveyor />
    </>
  );
}

function Conveyor() {
  return (
    <div
      style={{
        position: "absolute",
        left: 48,
        top: 258,
        width: 404,
        height: 18,
        transform: "translateZ(6px)",
        overflow: "hidden",
        borderRadius: 999,
        background: "rgba(255,255,255,.04)",
        border: "1px solid rgba(255,255,255,.06)",
      }}
    >
      <div
        style={{
          position: "absolute",
          left: -120,
          top: 1,
          width: 120,
          height: 14,
          borderRadius: 999,
          background:
            "linear-gradient(90deg, rgba(92,200,255,.2), rgba(92,200,255,.85), rgba(255,255,255,.15))",
          boxShadow: "0 0 22px rgba(92,200,255,.35)",
          animation: "lo-belt 8s linear infinite",
        }}
      />
    </div>
  );
}
