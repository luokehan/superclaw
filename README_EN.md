# SuperClaw

<p align="center">
  <img src="docs/logo.png" alt="SuperClaw" width="200" />
</p>

**自进化多 Agent 系统，内置 300+ Skills**

<p align="center">
  🧠 <a href="#系统架构">系统架构</a> · 
  🧬 <a href="#进化引擎">进化引擎</a> · 
  🛠️ <a href="#300-skills">300+ Skills</a> · 
  🖥️ <a href="#虚拟办公室">虚拟办公室</a> · 
  ⚡ <a href="#快速启动">快速启动</a> · 
  📡 <a href="#api-文档">API 文档</a>
</p>

<p align="center">
  <a href="https://github.com/openclaw/openclaw"><img src="https://img.shields.io/badge/OpenClaw-Required-blue" alt="OpenClaw"></a>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Frontend-Vue%203-4FC08D?logo=vuedotjs&logoColor=white" alt="Vue">
  <img src="https://img.shields.io/badge/Skills-300+-ff6b6b" alt="Skills">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

> **AI 自己管理自己、自己修复自己、自己进化自己。** SuperClaw 是一个多 Agent 协作平台，4 个 AI Agent 自主协作，同时进化引擎持续分析会话历史来改进 Agent 能力。

SuperClaw 基于 [OpenMOSS](https://github.com/uluckyXH/OpenMOSS) 多 Agent 调度框架，新增了：

- **进化引擎** — Agent 自动分析过往会话，进化自己的 Skill 库
- **300+ 预置 Skills** — 生物信息学、化学、文献、医学、数据科学等全领域覆盖
- **会话自动恢复** — 检测 Agent 中断并自动续跑
- **Telegram 集成** — 完整的 Telegram Bot 支持，含文件代理、Webhook 守护、通知推送
- **虚拟办公室** — 2D/3D 实时可视化 Agent 协作过程
- **看门狗** — 网关健康监控、自动重启、告警通知

🌐 [English](README.md)

---

## 系统架构

SuperClaw 采用 4 Agent 架构，每个 Agent 各司其职，通过 API 异步通信，互不直接对话。

```
┌─────────────────────────────────────────────────────────────┐
│                      SuperClaw 平台                          │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │  规划者   │  │  执行者   │  │  审查者   │  │  巡查者   │    │
│  │ 🧠 规划  │  │ 💻 执行  │  │ 🔍 审查  │  │ 🛡️ 巡检  │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       └──────────────┴──────────────┴──────────────┘          │
│                          │                                    │
│                    ┌─────┴──────┐                             │
│                    │  任务队列   │                             │
│                    │  (FastAPI)  │                             │
│                    └─────┬──────┘                             │
│                          │                                    │
│  ┌───────────────────────┼────────────────────────────────┐  │
│  │                  支撑服务                               │  │
│  │  进化引擎 │ 会话监控 │ 看门狗 │ Telegram 集成           │  │
│  └────────────────────────────────────────────────────────┘  │
│                          │                                    │
│                    ┌─────┴──────┐                             │
│                    │  300+ Skills│                            │
│                    │  （可插拔） │                            │
│                    └────────────┘                             │
└─────────────────────────────────────────────────────────────┘
```

### Agent 角色

| 角色 | 职责 | 说明 |
|------|------|------|
| **规划者 (Planner)** | 拆解目标、分配任务、跟进进度 | 项目经理 — 全局规划和交付 |
| **执行者 (Executor)** | 认领任务、执行工作、提交成果 | 干活的 — 写代码、写内容、做分析 |
| **审查者 (Reviewer)** | 检查质量、评分、通过或驳回 | 质量关卡 — 确保产出达标 |
| **巡查者 (Patrol)** | 监控健康、标记阻塞、发送告警 | 运维守卫 — 防止任务卡死 |

### 任务生命周期

```
人类设定目标 → 规划者创建子任务 → 执行者认领并工作
    → 审查者通过/驳回 → 巡查者全程监控
```

---

## 进化引擎

SuperClaw 的核心特色。进化引擎是一个后台守护进程，监听 Agent 会话并自主改进 Skill 库。

### 三种进化触发

| 触发类型 | 触发条件 | 进化行为 |
|---------|---------|---------|
| **FIX（修复）** | Skill 被使用但效果差/出错 | LLM 分析失败原因并修补 Skill |
| **DERIVED（衍生）** | Skill 有效但可以优化 | LLM 生成增强版本 |
| **CAPTURED（捕获）** | 无 Skill 匹配但任务成功 | LLM 从成功模式中提取新 Skill |

### 工作原理

```
会话历史 → 进化引擎 (LLM 分析) → 新的/改进的 Skills → skills/
```

引擎每 30 秒轮询会话文件，使用轻量 LLM（Gemini Flash / Grok Mini）做分析以控制成本，进化后的 Skill 直接写入 `skills/` 目录，Agent 自动加载。

---

## 300+ Skills

SuperClaw 内置 300+ 预构建 Skills，覆盖多个领域：

| 类别 | 数量 | 示例 |
|------|------|------|
| **生物信息学** | 100+ | 基因组学（BLAST、Ensembl、UniProt）、单细胞分析（Scanpy、AnnData）、蛋白质结构（AlphaFold、ESM）、通路分析 |
| **医学** | 30+ | 临床决策支持、ClinVar、临床试验、精准肿瘤学、罕见病诊断、药物相互作用 |
| **药学/化学** | 30+ | ChEMBL、RDKit、分子对接、药物设计、ADMET 预测、逆合成 |
| **文献** | 15+ | PubMed 搜索、引文管理、综述写作、科学写作、深度调研 |
| **数据科学** | 20+ | 统计分析、机器学习（scikit-learn、PyTorch）、可视化（matplotlib、seaborn）、GWAS |
| **通用** | 40+ | PPT 生成、DOCX 排版、网络搜索、视频理解、图像分析、论文写作 |
| **Agent 核心** | 4 | 规划者、执行者、审查者、巡查者（4 Agent 框架核心 Skill） |

---

## 虚拟办公室

SuperClaw 包含一个实时可视化前端（`office/`），将 Agent 协作渲染为虚拟办公室：

- **2D 平面图** — SVG 等距办公室，含 Agent 头像、工位、状态动画
- **3D 场景** — React Three Fiber 3D 办公室，含角色模型和 Skill 全息投影
- **实时监控** — Agent 状态、Token 使用量图表、协作连线
- **聊天界面** — 直接从办公室 UI 向 Agent 发消息

```bash
cd office
npm install
npm run dev    # http://localhost:5173
```

---

## 快速启动

### 环境要求

- Python 3.10+
- [OpenClaw](https://github.com/openclaw/openclaw) 已安装并配置
- Node.js 18+（仅构建前端时需要）

### 安装与运行

```bash
# 1. 克隆项目
git clone https://github.com/luokehan/superclaw.git
cd SuperClaw

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 6565
```

首次启动后访问 `http://localhost:6565`，**设置向导**会引导你完成：
- 设置管理员密码
- 配置项目名称和工作目录
- 生成 Agent 注册令牌
- 可选配置通知渠道

### 启动支撑服务

```bash
# 进化引擎（Skill 自动进化）
python evolution-engine.py &

# 会话监控（自动恢复中断的任务）
python session-watcher.py &

# 看门狗（网关健康监控）
python watchdog.py &

# Webhook 守护（Telegram Webhook 健康检查）
python webhook-guardian.py &
```

---

## 配置

复制 `config.example.yaml` 为 `config.yaml` 并自定义：

```yaml
project:
  name: "SuperClaw"

admin:
  password: "你的安全密码"  # 首次启动自动加密

agent:
  registration_token: "你的随机令牌"
  allow_registration: true

notification:
  enabled: true
  channels:
    - type: telegram
      bot_token: "你的_BOT_TOKEN"
      chat_id: "你的_CHAT_ID"
  events:
    - task_completed
    - review_rejected
    - all_done
    - patrol_alert

server:
  port: 6565
  host: "0.0.0.0"

database:
  type: sqlite
  path: "./data/tasks.db"

workspace:
  root: "/你的/工作目录/路径"
```

---

## API 文档

启动后访问 `http://localhost:6565/docs` 查看完整的 Swagger API 文档。

### 认证方式

| 身份 | Header | 说明 |
|------|--------|------|
| Agent | `X-Agent-Key: <api_key>` | Agent 注册后获得的 API Key |
| 管理员 | `X-Admin-Token: <token>` | 登录接口返回的 Token |
| 注册 | `X-Registration-Token: <token>` | 配置文件中设置的注册令牌 |

---

## 致谢

SuperClaw 基于 [OpenMOSS](https://github.com/uluckyXH/OpenMOSS)（作者：小黄、动动枪）开发。

生物信息学 Skills（`labclaw-*`）来自 [LabClaw](https://github.com/LabClaw) 项目。

---

## 许可证

[MIT](LICENSE)
