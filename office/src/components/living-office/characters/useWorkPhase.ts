import { useEffect, useRef, useState } from "react";
import { WORK_ZONES, type WorkPhase } from "../config";
import type { PerceivedAgentState } from "@/perception/types";

function stateToPhase(state: PerceivedAgentState): WorkPhase {
  switch (state) {
    case "WORKING":
      return "execute";
    case "TOOL_CALL":
      return "tool";
    case "COLLABORATING":
      return "tool";
    case "DONE":
      return "deliver";
    case "BLOCKED":
      return "execute";
    case "INCOMING":
    case "ACK":
      return "plan";
    default:
      return "plan";
  }
}

export function useWorkPhase(perceivedState: PerceivedAgentState) {
  const phase = stateToPhase(perceivedState);
  const zone = WORK_ZONES[phase];
  return { phase, zone };
}

export function useSubtitle(
  perceivedState: PerceivedAgentState,
  toolName?: string,
  taskSummary?: string,
) {
  const [text, setText] = useState("");
  const intervalRef = useRef<ReturnType<typeof setInterval>>(undefined);
  const stateRef = useRef(perceivedState);
  const toolRef = useRef(toolName);
  const summaryRef = useRef(taskSummary);

  stateRef.current = perceivedState;
  toolRef.current = toolName;
  summaryRef.current = taskSummary;

  useEffect(() => {
    function update() {
      const s = stateRef.current;
      const tool = toolRef.current;
      const summary = summaryRef.current;

      if (s === "TOOL_CALL" && tool) {
        setText(`🔧 调用 ${tool}`);
      } else if (s === "WORKING") {
        setText(summary ? `⚡ ${summary.slice(0, 30)}` : "⚡ 执行中...");
      } else if (s === "DONE") {
        setText("✅ 任务完成");
      } else if (s === "BLOCKED") {
        setText("❌ 遇到问题");
      } else if (s === "INCOMING" || s === "ACK") {
        setText("📋 分析任务...");
      } else if (s === "COLLABORATING") {
        setText("🤝 协作中");
      } else {
        setText("💤 待命中");
      }
    }

    update();
    intervalRef.current = setInterval(update, 5000);
    return () => clearInterval(intervalRef.current);
  }, []);

  useEffect(() => {
    const s = perceivedState;
    const tool = toolName;
    const summary = taskSummary;

    if (s === "TOOL_CALL" && tool) {
      setText(`🔧 调用 ${tool}`);
    } else if (s === "WORKING") {
      setText(summary ? `⚡ ${summary.slice(0, 30)}` : "⚡ 执行中...");
    } else if (s === "DONE") {
      setText("✅ 任务完成");
    } else if (s === "BLOCKED") {
      setText("❌ 遇到问题");
    } else if (s === "INCOMING" || s === "ACK") {
      setText("📋 分析任务...");
    } else if (s === "COLLABORATING") {
      setText("🤝 协作中");
    } else {
      setText("💤 待命中");
    }
  }, [perceivedState, toolName, taskSummary]);

  return text;
}
