import { LOUNGE_SOFA_POSITIONS } from "../characters/constants";

function Sofa({ left, top }: { left: number; top: number }) {
  return (
    <div
      style={{
        position: "absolute",
        left,
        top,
        width: 72,
        height: 38,
        transform: "translateZ(8px)",
      }}
    >
      {/* Seat cushion */}
      <div
        style={{
          position: "absolute",
          left: 4,
          top: 10,
          width: 64,
          height: 24,
          borderRadius: 12,
          background:
            "linear-gradient(180deg, rgba(143,125,255,.18), rgba(92,200,255,.08))",
          border: "1px solid rgba(143,125,255,.15)",
          boxShadow:
            "0 4px 12px rgba(0,0,0,.2), inset 0 1px 0 rgba(255,255,255,.06)",
        }}
      />
      {/* Back rest */}
      <div
        style={{
          position: "absolute",
          left: 8,
          top: 2,
          width: 56,
          height: 12,
          borderRadius: "10px 10px 4px 4px",
          background:
            "linear-gradient(180deg, rgba(143,125,255,.25), rgba(143,125,255,.12))",
          border: "1px solid rgba(143,125,255,.12)",
        }}
      />
      {/* Left arm */}
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 8,
          width: 8,
          height: 22,
          borderRadius: "6px 0 0 6px",
          background: "rgba(143,125,255,.14)",
          border: "1px solid rgba(143,125,255,.10)",
        }}
      />
      {/* Right arm */}
      <div
        style={{
          position: "absolute",
          right: 0,
          top: 8,
          width: 8,
          height: 22,
          borderRadius: "0 6px 6px 0",
          background: "rgba(143,125,255,.14)",
          border: "1px solid rgba(143,125,255,.10)",
        }}
      />
    </div>
  );
}

function CoffeeTable({ left, top }: { left: number; top: number }) {
  return (
    <div
      style={{
        position: "absolute",
        left,
        top,
        width: 32,
        height: 20,
        transform: "translateZ(6px)",
        borderRadius: 8,
        background:
          "linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.02))",
        border: "1px solid rgba(255,255,255,.06)",
        boxShadow: "0 4px 10px rgba(0,0,0,.15)",
      }}
    >
      {/* Cup */}
      <div
        style={{
          position: "absolute",
          left: 10,
          top: 4,
          width: 12,
          height: 12,
          borderRadius: "50%",
          background: "rgba(247,185,85,.2)",
          border: "1px solid rgba(247,185,85,.15)",
        }}
      />
    </div>
  );
}

function Plant({ left, top }: { left: number; top: number }) {
  return (
    <div
      style={{
        position: "absolute",
        left,
        top,
        width: 22,
        height: 30,
        transform: "translateZ(10px)",
      }}
    >
      {/* Pot */}
      <div
        style={{
          position: "absolute",
          left: 4,
          bottom: 0,
          width: 14,
          height: 12,
          borderRadius: "3px 3px 6px 6px",
          background: "rgba(180,120,70,.3)",
          border: "1px solid rgba(180,120,70,.2)",
        }}
      />
      {/* Leaves */}
      <div
        style={{
          position: "absolute",
          left: 2,
          top: 0,
          width: 18,
          height: 18,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(52,211,153,.35), rgba(22,163,74,.15))",
        }}
      />
    </div>
  );
}

export function LoungeArea() {
  return (
    <>
      {LOUNGE_SOFA_POSITIONS.map((pos, i) => (
        <Sofa key={`sofa-${String(i)}`} left={pos.left} top={pos.top} />
      ))}

      <CoffeeTable left={240} top={755} />
      <CoffeeTable left={680} top={755} />
      <CoffeeTable left={1100} top={755} />
      <CoffeeTable left={360} top={835} />
      <CoffeeTable left={800} top={835} />

      <Plant left={60} top={710} />
      <Plant left={1350} top={710} />
      <Plant left={500} top={845} />
      <Plant left={960} top={845} />
    </>
  );
}
