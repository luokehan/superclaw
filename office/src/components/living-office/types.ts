export type DeskStatus = "idle" | "busy" | "blocked" | "heartbeat";

export interface DeskConfig {
  id: string;
  agentName: string;
  role: string;
  position: { left: number; top: number };
  status?: DeskStatus;
  bubble?: string;
}

export interface ZoneConfig {
  id: string;
  label: string;
  position: { left: number; top: number };
  size: { width: number; height: number };
}

export interface CronTask {
  time: string;
  name: string;
  status: string;
}

export interface MemoryEntry {
  text: string;
  tag: string;
}

export interface OpsRule {
  text: string;
  tag: string;
}

export interface ProjectTask {
  title: string;
  subtitle: string;
}

export interface BusLine {
  title: string;
  detail: string;
}
