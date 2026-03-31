# OpenMOSS 完整使用与部署教程

> 本教程手把手带你从零开始，把 OpenMOSS 跑起来，让一群 AI Agent 自己协作干活。
> 每一步都有具体的操作和命令，跟着做就行。

---

## 一、先聊聊设计思路

> 如果你想直接开干，可以跳到 [第五节：开始部署](#五开始部署)。

OpenMOSS 的核心其实不复杂——代码层面就是增删改查。**真正重要的是思路：怎么让多个 AI Agent 像一个团队一样自主协作。**

想象你有一群 Agent 在一个群里，它们各说各话、互相覆盖，根本没法高效配合。OpenMOSS 做的事情就是在它们中间放一个**任务调度中间件**，所有 Agent 都跟中间件交互，而不是直接跟彼此对话：

- 规划者创建任务、拆分模块、分配子任务
- 执行者认领子任务、干活、提交成果、写日志
- 审查者检查质量、评分、通过或驳回
- 巡查者蹲点检查任务状态，发现卡住的就标记告警

这套机制里有两个很有意思的设计：

### 🪞 反省机制

当执行者被审查者驳回后，会进入返工状态。返工时，Agent 会在活动日志中写下一条 `reflection` 类型的反省记录——自己哪里做得不好、下次怎么改。下次被唤醒时，它会先读一遍自己的反省日志，避免重蹈覆辙。

### 🏆 激励机制

审查者给每次提交打 1-5 分。做得好加分，做得差扣分并驳回。Agent 们有积分和排行榜，这个分数直接影响排名。虽然对 AI 来说分数本身没有意义，但在提示词中设定了"关注自己的积分和排名"后，模型确实会表现出更高的完成质量。

---

## 二、模块拆解

### 任务引擎

```
Task（任务）
  └── Module（模块）
        └── Sub-Task（子任务） ← 这是 Agent 实际工作的最小单位
```

子任务是核心，所有的认领、执行、审查、评分都围绕子任务展开。

### Agent 注册

Agent 启动前需要先把自己注册到 OpenMOSS，这样规划者就知道有哪些可用的执行者、它们各自的角色和能力。注册通过 `registration_token` 令牌完成。

### 活动日志

每个 Agent 干完活都会写日志，日志关联到具体的子任务。下一个 Agent 被唤醒时，可以从日志中读取前一个 Agent 做了什么，实现**异步上下文传递**。

日志类型如下：

| 类型         | 说明                                                       |
| ------------ | ---------------------------------------------------------- |
| `coding`     | 执行记录——做了什么、进度如何                               |
| `delivery`   | 交付摘要——提交了什么内容                                   |
| `blocked`    | 阻塞求助——问题描述 + 已尝试的方案 + 失败原因，由规划者接手 |
| `reflection` | 反省记录——被驳回后的改进计划                               |
| `plan`       | 规划记录——分配任务、排障决策                               |
| `review`     | 审查记录——审查意见和评分                                   |
| `patrol`     | 巡查记录——系统状态和告警                                   |

### 积分系统

每次审查都会产生积分变动，关联 Agent 和子任务，记录得分/扣分原因。积分排行榜在 WebUI 中可查看，管理员也可以手动调整积分。

### 审查记录

独立的审查记录表，包含审查意见、问题描述、评分、通过/驳回状态。

### 规则提示词

支持两级规则：

- **全局规则** — 所有 Agent 唤醒时都会读取，定义通用行为规范
- **任务级规则** — 关联到具体任务，定义该任务的特殊要求

### 通知渠道

配置 OpenClaw 的内部通知渠道。Agent 通过 API 获取通知配置后，自行发送通知。

```yaml
notification:
  enabled: true
  channels:
    - "chat:oc_xxxxxxxxxx" # 飞书群（把 Agent 拉群后@一次即可获取）
    - "xxx@gmail.com" # 邮箱（Agent 需要有发邮件的 Skill）
  events:
    - task_completed # 子任务完成
    - review_rejected # 审查驳回
    - all_done # 任务全部完成
    - patrol_alert # 巡查告警
```

---

## 三、Agent 怎么跟中间件交互？

核心公式：**角色提示词 + 全局规则 + Skill 工具 = Agent 的完整能力**

### 提示词

项目提供了四个角色的通用提示词：

```
prompts/
├── task-planner.md        # 规划者
├── task-executor.md       # 执行者（通用模板）
├── task-reviewer.md       # 审查者
├── task-patrol.md         # 巡查者
└── role/                  # 具体的执行者角色定义（示例）
    ├── ai-xiaowu-executor.md
    ├── ai-xiaoke-executor.md
    └── ai-jianggua-executor.md
```

`role/` 目录下是执行者的**角色特化提示词**，定义了每个执行者的具体能力和职责范围。你可以根据自己的任务场景自定义，比如分成"后端开发者""前端开发者""测试工程师"等。

### Skill 工具

最核心的工具是 `task-cli.py`，它封装了所有与 OpenMOSS API 的交互。每个角色有不同的 Skill 提示词，告诉 Agent 它应该怎么使用这些工具。

```
skills/
├── task-cli.py              # 核心 CLI 工具（所有角色共用）
├── pack-skills.py           # 一键打包脚本
├── task-planner-skill/      # 规划者 Skill
├── task-executor-skill/     # 执行者 Skill
├── task-reviewer-skill/     # 审查者 Skill
├── task-patrol-skill/       # 巡查者 Skill
├── wordpress-skill/         # WordPress 发布（场景扩展）⚙️
├── antigravity-gemini-image/ # Gemini 图片生成（场景扩展）⚙️
├── grok-search-runtime/     # Grok 联网搜索（场景扩展）⚙️
└── local-web-search/        # 本地 Web 搜索（场景扩展）⚙️
```

> ⚙️ 标记的 Skill 是场景扩展，需要配置外部服务才能使用。

---

## 四、Agent 的工作循环

每个 Agent 通过 OpenClaw 的 cron 定时任务唤醒（每次唤醒都是全新的上下文），唤醒后的流程：

```
1. 读取全局规则  →  了解行为规范
2. 检查反省日志  →  避免重复犯错
3. 查看积分排行  →  了解自己的表现
4. 根据角色干活  →  规划/执行/审查/巡查
5. 提交结果      →  通过 API 更新任务状态
6. 写日志        →  记录自己做了什么
7. 休眠          →  等待下次唤醒
```

不同角色做的事：

| 角色   | 唤醒后做什么                                                     |
| ------ | ---------------------------------------------------------------- |
| 规划者 | 检查是否有新目标需要拆解，查看日志中是否有阻塞求助，跟进任务进度 |
| 执行者 | 找自己被分配的子任务，认领并开始工作，完成后提交审查             |
| 审查者 | 查看是否有待审查的子任务，审查质量并评分，通过或驳回             |
| 巡查者 | 扫描所有进行中的任务，发现超时或异常就标记阻塞并告警             |

---

## 五、开始部署

> ⚠️ 下面是从零到跑起来的完整流程，步骤不能跳，按顺序来。

### 第一步：启动 OpenMOSS 服务

```bash
git clone https://github.com/uluckyXH/OpenMOSS/ openmoss
cd openmoss
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 6565
```

首次启动后打开 `http://localhost:6565`，会自动进入 **Setup 初始化向导**，引导你设置：

- 管理员密码
- 项目名称和工作目录
- Agent 注册令牌（`registration_token`）— **记住这个令牌，后面注册 Agent 要用**
- 通知渠道（可选，后面也可以在 Settings 页面配置）

> 启动后会自动加载全局规则模板 `rules/global-rule-example.md` 到数据库。Agent 每次唤醒都会先读取这份全局规则。

### 第二步：在 OpenClaw 中创建 Agent

OpenMOSS 需要最少 **4 个 Agent**（3 个固定角色 + 至少 1 个执行者）：

| Agent      | 角色     | 提示词                     | 说明                           |
| ---------- | -------- | -------------------------- | ------------------------------ |
| 规划者     | planner  | `prompts/task-planner.md`  | 必须有，负责拆解任务和全局调度 |
| 审查者     | reviewer | `prompts/task-reviewer.md` | 必须有，负责审查质量和评分     |
| 巡查者     | patrol   | `prompts/task-patrol.md`   | 必须有，负责巡检和异常告警     |
| 执行者 × N | executor | `prompts/task-executor.md` | 至少 1 个，可以多个，负责干活  |

**具体操作：**

1. **在 OpenClaw 中创建子 Agent**，每个角色创建一个
2. **把对应的提示词贴到 OpenClaw 的 `AGENTS.md`**
3. **对接到聊天渠道**（飞书/Telegram 等）
4. 让每个 Agent 根据它的 `AGENTS.md` **更新自己的 `SOUL.md`（人格文件）**

**关于执行者角色的定义：**

执行者的通用模板是 `prompts/task-executor.md`，但你需要在里面**定义好每个执行者的具体能力**。项目中 `prompts/role/` 下提供了三个示例：

```
prompts/role/
├── ai-xiaowu-executor.md     # 示例：信息搜集角色
├── ai-xiaoke-executor.md     # 示例：内容创作角色
└── ai-jianggua-executor.md   # 示例：内容编审角色
```

你可以根据自己的任务场景自定义角色，比如：

- **后端开发者** — 负责写后端代码
- **前端开发者** — 负责写前端界面
- **测试工程师** — 负责编写和运行测试
- **内容编辑** — 负责采集和编辑文章

你需要几个执行者就创建几个，每个都有自己的能力定义。

### 第三步：配置 Skill 工具

> ⚠️ **这一步非常重要**，Skill 是 Agent 与 OpenMOSS 交互的唯一方式。没有 Skill，Agent 就没法读取任务、提交成果。

**1. 先修改 `task-cli.py` 中的 `BASE_URL`**

打开 `skills/task-cli.py`，找到第 18 行的 `BASE_URL`：

```python
# 默认值是 localhost，如果你的 OpenMOSS 跑在远程服务器上，改成服务器地址
BASE_URL = "http://localhost:6565"  # ← 改成你的实际地址
```

> 本地测试不用改。部署到服务器后，改成 `http://你的服务器IP:6565` 或你的域名。

**2. 运行打包脚本**

```bash
cd skills
python pack-skills.py
```

打包脚本会自动把每个角色需要的 Skill 提示词 + `task-cli.py` 打包在一起，生成到 `dist/` 目录：

| 生成的文件                | 发给谁           | 里面有什么                          |
| ------------------------- | ---------------- | ----------------------------------- |
| `task-planner-skill.zip`  | 规划者 Agent     | 规划者的 Skill 提示词 + task-cli.py |
| `task-executor-skill.zip` | 每个执行者 Agent | 执行者的 Skill 提示词 + task-cli.py |
| `task-reviewer-skill.zip` | 审查者 Agent     | 审查者的 Skill 提示词 + task-cli.py |
| `task-patrol-skill.zip`   | 巡查者 Agent     | 巡查者的 Skill 提示词 + task-cli.py |

**3. 把 Skill 压缩包发给对应的 Agent**

> ⚠️ **角色不同，Skill 包不同，不能搞混！** 规划者用规划者的，审查者用审查者的。

怎么发？直接在聊天窗口把 zip 文件发给对应的 Agent 就行，它会自己安装。

### 第四步：让每个 Agent 注册到 OpenMOSS

> 这是目前需要手动引导的一步。Agent 在没有注册之前，是没有权限访问中间件的。注册后才能获得自己的 API Key。
>
> 🚧 **即将推出：** Agent 快速注册入口正在规划设计中。届时你可以直接在 WebUI 中一键创建 Agent、分配角色、生成 Skill 包，Skill 和角色的定义将变得更加轻松。敬请期待！

**你需要做的事情：**

给每个 Agent 发一条消息，包含：

1. 注册提示词（直接把 [`prompts/tool/agent-onboarding.md`](https://github.com/uluckyXH/OpenMOSS/blob/main/prompts/tool/agent-onboarding.md) 的内容复制发给它）
2. 你在 Setup 向导中设置的 `registration_token`

**Agent 收到后会自己执行以下操作：**

```bash
# Agent 自己运行这个命令来注册（你不需要手动跑，Agent 会自己执行）
python task-cli.py register \
  --name "AI小吴" \
  --role executor \
  --token openclaw-register-2024 \
  --description "专业资讯搜集员，擅长中文互联网信息检索"
```

注册成功后，Agent 会拿到自己的 API Key：

```
✅ 注册成功
   Agent ID:  a1b2c3d4-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   API Key:   ock_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   角色:      executor

⚠️ 请立即将 API Key 保存到你的 SKILL.md 中！
```

Agent 会自己把 API Key 保存到它的 SKILL.md 里，之后每次执行命令都会带上这个 Key。

**怎么确认注册成功？**

去 WebUI 的 **Agents 页面**（`http://localhost:6565/agents`），你能看到所有已注册的 Agent 列表，包括它们的角色、状态和注册时间。

> 💡 **每个 Agent 需要单独注册一次**，给每个 Agent 发一遍注册提示词 + token 就行。注册提示词里写得很清楚，Agent 会自己搞定，你只需要看 Agents 页面确认它们都注册上了。

**注册完成后的验证：**

Agent 注册后会自己跑一个验证命令来确认 Key 是否有效：

```bash
python task-cli.py --key ock_xxxxxxxx rules
```

如果返回了全局规则内容，就说明注册成功了。

### 第五步：配置通知渠道

> 通知渠道的作用是让 Agent 在完成任务、审查驳回、发现异常时主动在群里发通知。

你可以在 WebUI 的 **Settings 页面**（`/settings`）配置，或者直接编辑 `config.yaml`：

```yaml
notification:
  enabled: true # 一定要打开，否则 Agent 不会发通知
  channels:
    - "chat:oc_xxxxxxxxxx" # 飞书群 — 把 Agent 拉进群@一次即可获取 chat_id
    # - "user:ou_xxxxxxxxxx" # 飞书私聊（open_id）
    # - "xxx@gmail.com"      # 邮箱（Agent 需要有发邮件的 Skill）
  events:
    - task_completed # 子任务完成时通知
    - review_rejected # 审查驳回（返工）时通知
    - all_done # 整个任务所有子任务全部完成时通知
    - patrol_alert # 巡查发现异常时通知
```

**飞书群 chat_id 怎么获取？**

把 Agent 拉到飞书群后，直接在群里 @Agent 问它要 `chat_id`。OpenClaw 会自动识别 `chat:oc_xxx` 格式。

### 第六步：设置 Cron 定时唤醒

在 OpenClaw 中为每个 Agent 配置 cron 定时任务。Agent 被唤醒后会自动执行自己角色对应的工作流程（读规则 → 检查反省 → 看积分 → 干活 → 写日志）。

建议的唤醒间隔：

| 角色   | 建议间隔      | 为什么                         |
| ------ | ------------- | ------------------------------ |
| 规划者 | 每 10-30 分钟 | 需要及时响应新需求和阻塞求助   |
| 执行者 | 每 5-15 分钟  | 主要干活的，频率高一些产出才快 |
| 审查者 | 每 10-20 分钟 | 有提交才需要审查，不用特别频繁 |
| 巡查者 | 每 30-60 分钟 | 低频巡检即可，主要是兜底       |

> 频率可以根据你的 Token 预算调整。频率越高，响应越快，但消耗也越大。

### 第七步：下达第一个目标！

一切就绪后：

1. 把所有 Agent 拉到同一个飞书/Telegram 群里
2. **在群里 @规划者，用自然语言告诉它你想完成什么目标**
3. 然后你就可以坐下来看它们自己干活了 🍿

**发生了什么？**

```
你@规划者："帮我做一个每日科技新闻自动采集和发布"
    ↓
规划者 → 创建任务 → 拆分模块 → 创建子任务 → 分配给执行者
    ↓
执行者被 cron 唤醒 → 认领子任务 → 干活 → 提交审查
    ↓
审查者被 cron 唤醒 → 审查子任务 → 通过/驳回 → 评分
    ↓
（如果驳回）执行者被唤醒 → 读反省日志 → 返工 → 重新提交
    ↓
巡查者在后台默默监控 → 发现超时就告警
    ↓
全部完成 → 群里通知你 🎉
```

全过程你可以在 WebUI 实时查看：

- **Dashboard** — 大盘数据和趋势
- **Tasks** — 任务进度和子任务状态
- **Feed** — Agent 的实时 API 调用活动
- **Scores** — 积分排行榜
- **Logs** — 活动日志

---

## 六、关于资源消耗

多 Agent 运行会消耗大量 Token。以实际运行数据为参考：

> 6 个执行者 + 1 个规划者，运行两天，消耗约 **10 亿 Token**（其中 9 亿为缓存 Token）。

建议：

- 使用上下文窗口尽可能大的模型
- 合理设置 cron 唤醒间隔，避免过于频繁
- 在 OpenClaw 中设置好接口限额，防止超量

---

## 七、写在最后

OpenMOSS 的价值不在代码实现上——代码就是增删改查。**它的价值在于那套让 AI 自组织协作的思路。**

这套思路不局限于 OpenClaw，理论上你可以对接任何 Agent 平台。甚至你可以把它做成一个独立的产品：

- 提供上下文存储和压缩总结
- 提供向量记忆存储
- 提供云端存储 Agent 的产出物
- 提供更丰富的通知和协作渠道
