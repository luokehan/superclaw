import { ZONE_CONFIGS } from "../config";
import { ProjectRoom } from "../panels/ProjectRoom";
import { ZonePanel } from "./ZonePanel";

export function ProjectZone() {
  const cfg = ZONE_CONFIGS.project;

  return (
    <>
      <ZonePanel config={cfg} />
      <ProjectRoom />
    </>
  );
}
