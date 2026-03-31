import { useEffect, useState } from "react";

interface DeskBubbleProps {
  text: string;
  duration?: number;
}

export function DeskBubble({ text, duration = 2600 }: DeskBubbleProps) {
  const [visible, setVisible] = useState(false);
  const [fading, setFading] = useState(false);

  useEffect(() => {
    if (!text) {
      setVisible(false);
      return;
    }

    setVisible(true);
    setFading(false);

    const fadeTimer = setTimeout(() => setFading(true), duration - 350);
    const hideTimer = setTimeout(() => setVisible(false), duration);

    return () => {
      clearTimeout(fadeTimer);
      clearTimeout(hideTimer);
    };
  }, [text, duration]);

  if (!visible || !text) return null;

  return (
    <div
      style={{
        position: "absolute",
        left: "50%",
        top: -22,
        transform: "translateX(-50%) translateZ(20px) translateY(-6px)",
        padding: "7px 10px",
        borderRadius: 999,
        whiteSpace: "nowrap",
        fontSize: 16,
        color: "#eef7ff",
        background: "rgba(8, 18, 32, .85)",
        border: "1px solid rgba(255,255,255,.08)",
        boxShadow: "0 14px 30px rgba(0,0,0,.28)",
        animation: fading
          ? "lo-bubble-out 0.35s ease forwards"
          : "lo-bubble-in 0.35s ease forwards",
        pointerEvents: "none",
      }}
    >
      {text}
    </div>
  );
}
