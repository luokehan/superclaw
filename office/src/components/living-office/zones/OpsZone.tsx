import { ZONE_CONFIGS } from "../config";
import { OpsBoard } from "../panels/OpsBoard";
import { ZonePanel } from "./ZonePanel";

export function OpsZone() {
  const cfg = ZONE_CONFIGS.ops;

  return (
    <>
      <ZonePanel config={cfg} />
      <OpsBoard />
    </>
  );
}
