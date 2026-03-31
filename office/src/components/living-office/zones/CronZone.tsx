import { ZONE_CONFIGS } from "../config";
import { BroadcastBeacon } from "../panels/BroadcastBeacon";
import { CronBoard } from "../panels/CronBoard";
import { ZonePanel } from "./ZonePanel";

export function CronZone() {
  const cfg = ZONE_CONFIGS.cron;

  return (
    <>
      <ZonePanel config={cfg} />
      <CronBoard />
      <BroadcastBeacon />
    </>
  );
}
