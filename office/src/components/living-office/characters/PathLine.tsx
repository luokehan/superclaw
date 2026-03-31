import { useEffect, useState } from "react";
import type { Position2D } from "./constants";

interface PathLineProps {
  from: Position2D;
  to: Position2D;
  durationMs?: number;
}

const FADE_DELAY_MS = 1300;

export function PathLine({ from, to, durationMs = FADE_DELAY_MS }: PathLineProps) {
  const [fading, setFading] = useState(false);
  const [removed, setRemoved] = useState(false);

  useEffect(() => {
    const fadeTimer = setTimeout(() => setFading(true), durationMs);
    const removeTimer = setTimeout(() => setRemoved(true), durationMs + 400);
    return () => {
      clearTimeout(fadeTimer);
      clearTimeout(removeTimer);
    };
  }, [durationMs]);

  if (removed) return null;

  const { distance, angle } = computeLineGeometry(from, to);

  return (
    <div
      className={`lo-path-line ${fading ? "lo-path-fading" : ""}`}
      style={{
        position: "absolute",
        left: from.left,
        top: from.top,
        width: distance,
        transform: `rotate(${angle}deg) translateZ(10px)`,
      }}
    />
  );
}

// Exported for testing
export function computeLineGeometry(
  from: Position2D,
  to: Position2D,
): { distance: number; angle: number } {
  const dx = to.left - from.left;
  const dy = to.top - from.top;
  const distance = Math.sqrt(dx * dx + dy * dy);
  const angle = (Math.atan2(dy, dx) * 180) / Math.PI;
  return { distance, angle };
}
