import { ZONE_CONFIGS } from "../config";
import { ZonePanel } from "./ZonePanel";
import { GlassPanel } from "../panels/GlassPanel";

const CAPABILITIES = [
  { icon: "🔍", name: "深度搜索", desc: "Grok + OpenCLI 多平台", color: "#5cc8ff" },
  { icon: "📊", name: "PPT 生成", desc: "officecli + Morph 动画", color: "#a78bfa" },
  { icon: "📝", name: "文档写作", desc: "DOCX / 论文 / 报告", color: "#34d399" },
  { icon: "🖼️", name: "图片生成", desc: "Gemini 图片生成", color: "#fbbf24" },
  { icon: "📈", name: "数据分析", desc: "Python / R / 可视化", color: "#f472b6" },
  { icon: "🌐", name: "网站操作", desc: "OpenCLI + Chrome", color: "#67e8f9" },
  { icon: "🧬", name: "生信分析", desc: "238 个 LabClaw 技能", color: "#fb923c" },
  { icon: "✍️", name: "中文润色", desc: "Humanizer 去 AI 痕迹", color: "#8f7dff" },
  { icon: "📚", name: "学术检索", desc: "PubMed / arXiv / OpenAlex", color: "#ff73d1" },
  { icon: "💬", name: "Telegram", desc: "接收任务 / 汇报进度", color: "#29d391" },
];

export function LoungeZone() {
  const cfg = ZONE_CONFIGS.lounge;

  return (
    <>
      <ZonePanel config={cfg} />
      <GlassPanel
        style={{
          position: "absolute",
          left: 48,
          top: 678,
          width: 1364,
          height: 194,
          transform: "translateZ(16px)",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div style={{ padding: "12px 16px 8px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <b style={{ fontSize: 16, color: "#e9f2ff" }}>🦞 SuperClaw 能力矩阵</b>
          <span style={{ fontSize: 13, color: "var(--lo-muted)" }}>258 技能 · 10 就绪</span>
        </div>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(5, 1fr)",
            gap: 8,
            padding: "0 14px 14px",
            flex: 1,
            overflow: "hidden",
          }}
        >
          {CAPABILITIES.map((cap) => (
            <div
              key={cap.name}
              style={{
                padding: "8px 10px",
                borderRadius: 12,
                background: "rgba(255,255,255,.04)",
                border: `1px solid ${cap.color}22`,
                display: "flex",
                alignItems: "center",
                gap: 8,
                minWidth: 0,
              }}
            >
              <span style={{ fontSize: 20, flexShrink: 0 }}>{cap.icon}</span>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: cap.color, whiteSpace: "nowrap" }}>{cap.name}</div>
                <div style={{ fontSize: 11, color: "var(--lo-muted)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{cap.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </GlassPanel>
    </>
  );
}
