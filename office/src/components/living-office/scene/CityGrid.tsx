export function CityGrid() {
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundImage: [
          "linear-gradient(to right, rgba(255,255,255,.03) 1px, transparent 1px)",
          "linear-gradient(to bottom, rgba(255,255,255,.03) 1px, transparent 1px)",
        ].join(", "),
        backgroundSize: "60px 60px",
        opacity: 0.18,
      }}
    />
  );
}
