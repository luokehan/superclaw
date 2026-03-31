import { ZONE_CONFIGS } from "../config";
import { MemoryWall } from "../panels/MemoryWall";
import { ZonePanel } from "./ZonePanel";

export function MemoryZone() {
  const cfg = ZONE_CONFIGS.memory;

  return (
    <>
      <ZonePanel config={cfg} />
      <MemoryWall />
    </>
  );
}
