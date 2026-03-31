import { useProjectionStore } from "@/perception/projection-store";
import { GlassPanel } from "./GlassPanel";
import { PanelHead } from "./PanelHead";

interface MemoryWallProps {
  entries?: Array<{ text: string; tag: string }>;
}

const EMPTY_ENTRIES: Array<{ text: string; tag: string }> = [];

export function MemoryWall({ entries = EMPTY_ENTRIES }: MemoryWallProps) {
  const liveEntries = useProjectionStore((s) => s.sceneArea.memoryItems);
  const displayEntries = liveEntries.length > 0 ? liveEntries : entries;

  return (
    <GlassPanel
      style={{
        position: "absolute",
        left: 1068,
        top: 455,
        width: 344,
        height: 110,
        transform: "translateZ(16px)",
      }}
    >
      <PanelHead title="工作记忆" subtitle="上下文 / 事实 / 经验" />
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 7,
          padding: "0 14px 14px",
        }}
      >
        {displayEntries.length > 0 ? (
          displayEntries.slice(-3).reverse().map((entry) => (
            <div
              key={entry.text}
              style={{
                display: "flex",
                justifyContent: "space-between",
                gap: 10,
                fontSize: 16,
                padding: "7px 9px",
                background: "rgba(255,255,255,.04)",
                borderRadius: 10,
              }}
            >
              <span style={{ color: "#e6eefc" }}>{entry.text}</span>
              <span style={{ color: "var(--lo-muted)" }}>{entry.tag}</span>
            </div>
          ))
        ) : (
          <div
            style={{
              fontSize: 16,
              padding: "7px 9px",
              background: "rgba(255,255,255,.04)",
              borderRadius: 10,
              color: "var(--lo-muted)",
            }}
          >
            SuperClaw 待命中，暂无活跃记忆
          </div>
        )}
      </div>
    </GlassPanel>
  );
}
