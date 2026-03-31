import { useMemo } from "react";

const PARTICLE_COUNT = 34;

interface Particle {
  left: string;
  top: string;
  duration: string;
  delay: string;
}

export function AmbientParticles() {
  const particles = useMemo<Particle[]>(() => {
    const result: Particle[] = [];
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      result.push({
        left: `${seededRandom(i, 0) * 100}vw`,
        top: `${seededRandom(i, 1) * 100}vh`,
        duration: `${20 + seededRandom(i, 2) * 30}s`,
        delay: `${-seededRandom(i, 3) * 40}s`,
      });
    }
    return result;
  }, []);

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        pointerEvents: "none",
        overflow: "hidden",
      }}
    >
      {particles.map((p, i) => (
        <i
          key={i}
          style={{
            position: "absolute",
            width: 2,
            height: 2,
            borderRadius: "50%",
            background: "rgba(255,255,255,.45)",
            boxShadow: "0 0 12px rgba(255,255,255,.3)",
            left: p.left,
            top: p.top,
            animation: `lo-float-star ${p.duration} linear infinite`,
            animationDelay: p.delay,
            opacity: 0.45,
          }}
        />
      ))}
    </div>
  );
}

function seededRandom(index: number, salt: number): number {
  const x = Math.sin(index * 9301 + salt * 49297 + 233280) * 49297;
  return x - Math.floor(x);
}
