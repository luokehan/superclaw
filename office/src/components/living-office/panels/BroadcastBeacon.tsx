export function BroadcastBeacon() {
  return (
    <div
      style={{
        position: "absolute",
        left: 1240,
        top: 258,
        width: 30,
        height: 30,
        borderRadius: "50%",
        transform: "translateZ(12px)",
        background:
          "radial-gradient(circle, rgba(247,185,85,.95), rgba(247,185,85,.25))",
        boxShadow: "0 0 24px rgba(247,185,85,.35)",
      }}
    >
      <Ring delay="0s" />
      <Ring delay="1.1s" />
    </div>
  );
}

function Ring({ delay }: { delay: string }) {
  return (
    <div
      style={{
        position: "absolute",
        inset: -8,
        borderRadius: "50%",
        border: "2px solid rgba(247,185,85,.22)",
        animation: "lo-rings 2.2s ease-out infinite",
        animationDelay: delay,
      }}
    />
  );
}
