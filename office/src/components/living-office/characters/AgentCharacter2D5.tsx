import { useEffect, useRef, useState } from "react";
import { transition, resetToIdle } from "@/perception/state-machine";
import type { PerceivedAgentState, PerceivedKind } from "@/perception/types";
import { CharacterBody, LOBSTER_SIZE } from "./CharacterBody";
import {
  AGENT_HOME_POSITIONS,
  CHARACTER_Z,
  IDLE_WANDER_DURATION,
  MOVE_DURATION_MS,
  MOVE_EASING,
  type Position2D,
} from "./constants";
import { useIdleBehavior } from "./useIdleBehavior";
import { WORK_ZONES } from "../config";

function stateToWorkPosition(state: PerceivedAgentState, home: Position2D): Position2D {
  switch (state) {
    case "INCOMING":
    case "ACK":
      return { left: WORK_ZONES.plan.left, top: WORK_ZONES.plan.top };
    case "WORKING":
      return { left: WORK_ZONES.execute.left, top: WORK_ZONES.execute.top };
    case "TOOL_CALL":
    case "COLLABORATING":
      return { left: WORK_ZONES.tool.left, top: WORK_ZONES.tool.top };
    case "DONE":
      return { left: WORK_ZONES.deliver.left, top: WORK_ZONES.deliver.top };
    case "BLOCKED":
      return { left: WORK_ZONES.execute.left, top: WORK_ZONES.execute.top };
    default:
      return home;
  }
}

interface AgentCharacter2D5Props {
  agentId: string;
  deskId: string;
  name: string;
  perceivedState: PerceivedAgentState;
  eventKind?: PerceivedKind;
  targetPosition?: Position2D;
  toolName?: string;
}

export function AgentCharacter2D5({
  agentId,
  deskId,
  name,
  perceivedState,
  eventKind,
  targetPosition,
  toolName,
}: AgentCharacter2D5Props) {
  const homePos = AGENT_HOME_POSITIONS[deskId] ?? { left: 0, top: 0 };
  const [internalState, setInternalState] = useState<PerceivedAgentState>("IDLE");
  const [cssClass, setCssClass] = useState("idle");
  const [walking, setWalking] = useState(false);
  const [position, setPosition] = useState<Position2D>(homePos);
  const prevStateRef = useRef<PerceivedAgentState>("IDLE");
  const walkTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const idle = useIdleBehavior(internalState, homePos);

  useEffect(() => {
    if (!eventKind) return;

    const result = transition(prevStateRef.current, eventKind);
    prevStateRef.current = result.nextState;
    setInternalState(result.nextState);
    setCssClass(result.visual.cssClass);

    const dest = stateToWorkPosition(result.nextState, homePos);
    if (dest.left !== position.left || dest.top !== position.top) {
      setWalking(true);
      setPosition(dest);
      clearTimeout(walkTimerRef.current);
      walkTimerRef.current = setTimeout(() => setWalking(false), MOVE_DURATION_MS);
    }
  }, [eventKind, targetPosition]);

  // Drive movement from perceivedState changes (main path for SuperClaw)
  const positionRef = useRef(position);
  positionRef.current = position;

  useEffect(() => {
    prevStateRef.current = perceivedState;
    setInternalState(perceivedState);
    setCssClass(getCssClassForState(perceivedState));

    const dest = stateToWorkPosition(perceivedState, homePos);
    const cur = positionRef.current;
    if (dest.left !== cur.left || dest.top !== cur.top) {
      setWalking(true);
      setPosition(dest);
      clearTimeout(walkTimerRef.current);
      walkTimerRef.current = setTimeout(() => setWalking(false), MOVE_DURATION_MS);
    }
  }, [perceivedState, homePos]);

  // DONE → IDLE auto-transition
  useEffect(() => {
    if (internalState !== "DONE") return;
    const timer = setTimeout(() => {
      const result = resetToIdle();
      prevStateRef.current = result.nextState;
      setInternalState(result.nextState);
      setCssClass(result.visual.cssClass);
      setWalking(true);
      setPosition(homePos);
      walkTimerRef.current = setTimeout(() => setWalking(false), MOVE_DURATION_MS);
    }, 3000);
    return () => clearTimeout(timer);
  }, [internalState, homePos]);

  // RETURNING → walk home
  useEffect(() => {
    if (internalState !== "RETURNING") return;
    setWalking(true);
    setPosition(homePos);
    const timer = setTimeout(() => {
      setWalking(false);
    }, MOVE_DURATION_MS);
    return () => clearTimeout(timer);
  }, [internalState, homePos]);

  useEffect(() => {
    return () => clearTimeout(walkTimerRef.current);
  }, []);

  // Compute final visual position = base + idle wander offset
  const isIdleState = internalState === "IDLE";
  const finalLeft = position.left + (isIdleState ? idle.wanderOffset.left : 0);
  const finalTop = position.top + (isIdleState ? idle.wanderOffset.top : 0);

  const isMoving = walking || idle.isWandering;
  const moveDuration = walking ? MOVE_DURATION_MS : IDLE_WANDER_DURATION;
  const moveEasing = walking ? MOVE_EASING : "ease-in-out";

  const stateClasses = [
    `lo-char-state-${cssClass}`,
    isMoving ? "lo-char-walking" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      data-agent-id={agentId}
      data-agent-state={internalState}
      className={`lo-character ${stateClasses}`}
      style={{
        position: "absolute",
        left: finalLeft - LOBSTER_SIZE / 2,
        top: finalTop - LOBSTER_SIZE / 2,
        width: LOBSTER_SIZE,
        transform: `translateZ(${CHARACTER_Z}px)`,
        transition: isMoving
          ? `left ${moveDuration}ms ${moveEasing}, top ${moveDuration}ms ${moveEasing}`
          : "left 0.3s ease, top 0.3s ease",
        zIndex: 100,
        pointerEvents: "none",
      }}
    >
      <CharacterBody
        name={name}
        agentId={agentId}
        cssClass={stateClasses}
        gazeDirection={idle.gazeDirection}
        state={internalState}
        toolName={toolName}
      />
    </div>
  );
}

function getCssClassForState(state: PerceivedAgentState): string {
  const map: Record<PerceivedAgentState, string> = {
    IDLE: "idle",
    INCOMING: "incoming",
    ACK: "ack",
    WORKING: "working",
    TOOL_CALL: "tool-call",
    WAITING: "waiting",
    COLLABORATING: "collaborating",
    RETURNING: "returning",
    DONE: "done",
    BLOCKED: "blocked",
    RECOVERED: "recovered",
  };
  return map[state];
}
