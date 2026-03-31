import type { DeskConfig, ZoneConfig } from "./types";

export const CANVAS_W = 1600;
export const CANVAS_H = 920;

// Top row: info panels
// Bottom: 4 themed rooms in a row
export const ZONE_CONFIGS: Record<string, ZoneConfig> = {
  gateway: {
    id: "gateway-zone",
    label: "Gateway 网关",
    position: { left: 30, top: 20 },
    size: { width: 440, height: 250 },
  },
  ops: {
    id: "ops-zone",
    label: "运行状态",
    position: { left: 490, top: 20 },
    size: { width: 540, height: 250 },
  },
  cron: {
    id: "cron-zone",
    label: "定时任务",
    position: { left: 1050, top: 20 },
    size: { width: 380, height: 250 },
  },
};

// 4 rooms side by side, each 330 wide
const ROOM_Y = 300;
const ROOM_H = 590;
const ROOM_W = 330;
const ROOM_GAP = 20;
const R1 = 50;
const R2 = R1 + ROOM_W + ROOM_GAP;
const R3 = R2 + ROOM_W + ROOM_GAP;
const R4 = R3 + ROOM_W + ROOM_GAP;

export const WORK_ZONES = {
  plan: {
    left: R1 + ROOM_W / 2,
    top: ROOM_Y + ROOM_H - 160,
    label: "📋 规划室",
    color: "#5cc8ff",
    room: { x: R1, y: ROOM_Y, w: ROOM_W, h: ROOM_H },
  },
  execute: {
    left: R2 + ROOM_W / 2,
    top: ROOM_Y + ROOM_H - 160,
    label: "⚡ 执行间",
    color: "#34d399",
    room: { x: R2, y: ROOM_Y, w: ROOM_W, h: ROOM_H },
  },
  tool: {
    left: R3 + ROOM_W / 2,
    top: ROOM_Y + ROOM_H - 160,
    label: "🔧 工具房",
    color: "#fbbf24",
    room: { x: R3, y: ROOM_Y, w: ROOM_W, h: ROOM_H },
  },
  deliver: {
    left: R4 + ROOM_W / 2,
    top: ROOM_Y + ROOM_H - 160,
    label: "✅ 交付台",
    color: "#a78bfa",
    room: { x: R4, y: ROOM_Y, w: ROOM_W, h: ROOM_H },
  },
} as const;

export type WorkPhase = keyof typeof WORK_ZONES;

export const DESK_CONFIGS: DeskConfig[] = [
  {
    id: "desk-superclaw",
    agentName: "🦞 SuperClaw",
    role: "superclaw",
    position: { left: WORK_ZONES.plan.left - 80, top: WORK_ZONES.plan.top - 90 },
  },
];
