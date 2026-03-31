import type { PerceivedAgentState } from "@/perception/types";
import { StatusIndicator } from "./StatusIndicator";
import {
  BODY_SIZE,
  CHARACTER_SIZE,
  SHADOW_COLOR,
  TAG_BG,
  TAG_COLOR,
} from "./constants";

const LOBSTER_IMG = "/superclaw-avatar.png?v=2";
export const LOBSTER_SIZE = CHARACTER_SIZE * 3;

interface CharacterBodyProps {
  name: string;
  agentId: string;
  cssClass: string;
  gazeDirection: number;
  state: PerceivedAgentState;
  toolName?: string;
}

export function CharacterBody({
  name,
  cssClass,
  state,
  toolName,
}: CharacterBodyProps) {
  return (
    <div
      className={`lo-char-body ${cssClass}`}
      style={{
        position: "relative",
        width: LOBSTER_SIZE,
        height: LOBSTER_SIZE + 20,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      <StatusIndicator state={state} toolName={toolName} />

      {/* Name tag */}
      <div
        className="lo-char-tag"
        style={{
          position: "absolute",
          top: -28,
          left: "50%",
          transform: "translateX(-50%) translateZ(18px)",
          fontSize: 13,
          fontWeight: 600,
          color: TAG_COLOR,
          background: TAG_BG,
          borderRadius: 8,
          padding: "1px 6px",
          whiteSpace: "nowrap",
          pointerEvents: "none",
          lineHeight: "14px",
          border: "1px solid rgba(255,255,255,0.08)",
        }}
      >
        {name}
      </div>

      {/* Lobster avatar */}
      <img
        src={LOBSTER_IMG}
        alt=""
        draggable={false}
        style={{
          width: LOBSTER_SIZE,
          height: LOBSTER_SIZE,
          objectFit: "contain",
          imageRendering: "auto",
          filter: "drop-shadow(0 3px 6px rgba(0,0,0,0.35))",
          zIndex: 2,
          pointerEvents: "none",
        }}
      />

      {/* Shadow */}
      <div
        className="lo-char-shadow"
        style={{
          width: BODY_SIZE + 10,
          height: 6,
          borderRadius: "50%",
          background: SHADOW_COLOR,
          filter: "blur(4px)",
          marginTop: -2,
          zIndex: 0,
        }}
      />

      {/* Status ring glow */}
      {state !== "IDLE" && state !== "DONE" && (
        <div
          className="lo-char-status-ring"
          style={{
            position: "absolute",
            bottom: 0,
            left: "50%",
            transform: "translateX(-50%)",
            width: BODY_SIZE + 14,
            height: 8,
            borderRadius: "50%",
            background: getStatusRingColor(state),
            filter: "blur(5px)",
            opacity: 0.6,
            zIndex: 0,
          }}
        />
      )}
    </div>
  );
}

function getStatusRingColor(state: PerceivedAgentState): string {
  switch (state) {
    case "WORKING":
    case "TOOL_CALL":
      return "rgba(92, 200, 255, 0.6)";
    case "BLOCKED":
      return "rgba(255, 102, 122, 0.7)";
    case "COLLABORATING":
      return "rgba(167, 139, 250, 0.6)";
    case "WAITING":
      return "rgba(148, 163, 184, 0.4)";
    case "INCOMING":
    case "ACK":
      return "rgba(92, 200, 255, 0.4)";
    case "RETURNING":
    case "RECOVERED":
      return "rgba(52, 211, 153, 0.5)";
    default:
      return "transparent";
  }
}
