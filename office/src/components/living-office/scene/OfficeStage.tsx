import type { ReactNode } from "react";
import { AmbientParticles } from "./AmbientParticles";
import { CityGrid } from "./CityGrid";
import { OfficeFloor } from "./OfficeFloor";

interface OfficeStageProps {
  children?: ReactNode;
}

export function OfficeStage({ children }: OfficeStageProps) {
  return (
    <div className="lo-world">
      <CityGrid />
      <div className="lo-office">
        <OfficeFloor />
        {children}
      </div>
      <AmbientParticles />
    </div>
  );
}
