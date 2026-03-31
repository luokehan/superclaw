# OpenMOSS Complete Deployment Guide

> This tutorial walks you through setting up OpenMOSS from scratch and getting a team of AI agents to collaborate autonomously.
> Every step includes specific commands — just follow along.

---

## 1. Design Philosophy

> If you want to jump straight into setup, skip to [Section 5: Start Deploying](#5-start-deploying).

The core of OpenMOSS is actually simple — at the code level, it's just CRUD. **What really matters is the idea: how to make multiple AI agents collaborate like a team.**

Imagine a group of agents in a chat room, talking over each other with no coordination. OpenMOSS solves this by placing a **task orchestration middleware** between them — all agents interact with the middleware, not directly with each other:

- **Planner** creates tasks, breaks them into modules, assigns sub-tasks
- **Executors** claim sub-tasks, do the work, submit deliverables, write logs
- **Reviewer** checks quality, scores work, approves or rejects
- **Patrol** monitors task status, flags stuck tasks, triggers alerts

Two particularly interesting mechanisms in this system:

### 🪞 Self-Reflection Mechanism

When an executor gets rejected by the reviewer, the sub-task enters a rework state. During rework, the agent writes a `reflection` log entry — what went wrong, what to improve. Next time it wakes up, it reads its own reflection logs first, avoiding the same mistakes.

### 🏆 Incentive Mechanism

The reviewer scores each submission from 1-5. Good work earns points; poor work gets deducted and rejected. Agents have scores and leaderboards. While scores are meaningless to AI per se, when you include "pay attention to your score and ranking" in the prompts, models demonstrably produce higher quality output.

---

## 2. Module Breakdown

### Task Engine

```
Task
  └── Module
        └── Sub-Task  ← the smallest unit agents actually work on
```

Sub-tasks are the core. All claiming, execution, review, and scoring revolves around sub-tasks.

### Agent Registration

Before starting work, each agent must register with OpenMOSS. This lets the planner know which executors are available and what their roles and capabilities are. Registration requires a `registration_token`.

### Activity Logs

Every agent writes logs after completing work. Logs are linked to specific sub-tasks. When the next agent wakes up, it can read what the previous agent did — enabling **asynchronous context passing**.

Log types:

| Type         | Description                                                                                   |
| ------------ | --------------------------------------------------------------------------------------------- |
| `coding`     | Execution record — what was done, progress status                                             |
| `delivery`   | Delivery summary — what was submitted                                                         |
| `blocked`    | Help request — problem description + attempted solutions + failure reason; planner takes over |
| `reflection` | Self-reflection — improvement plan after rejection                                            |
| `plan`       | Planning record — task assignments, troubleshooting decisions                                 |
| `review`     | Review record — review comments and scores                                                    |
| `patrol`     | Patrol record — system status and alerts                                                      |

### Scoring System

Each review generates score changes, linked to the agent and sub-task, with reasons documented. The leaderboard is visible in the WebUI, and admins can manually adjust scores.

### Review Records

A dedicated review records table with review comments, issue descriptions, scores, and approved/rejected status.

### Rule Prompts

Two levels of rules:

- **Global rules** — read by all agents on every wake-up, defining universal behavior standards
- **Task-level rules** — linked to specific tasks, defining task-specific requirements

### Notification Channels

Configure OpenClaw's internal notification channels. Agents fetch notification settings via API and send notifications themselves.

```yaml
notification:
  enabled: true
  channels:
    - "chat:oc_xxxxxxxxxx" # Lark/Feishu group (invite agent to group, @ once to get chat_id)
    - "xxx@gmail.com" # Email (agent needs email-sending Skill)
  events:
    - task_completed # Sub-task completed
    - review_rejected # Review rejected
    - all_done # All sub-tasks in a task completed
    - patrol_alert # Patrol alert
```

---

## 3. How Do Agents Interact With the Middleware?

Core formula: **Role prompt + Global rules + Skill tools = Agent's complete capabilities**

### Prompts

The project provides four role-specific prompts:

```
prompts/
├── task-planner.md        # Planner
├── task-executor.md       # Executor (generic template)
├── task-reviewer.md       # Reviewer
├── task-patrol.md         # Patrol
└── role/                  # Executor role specializations (examples)
    ├── ai-xiaowu-executor.md
    ├── ai-xiaoke-executor.md
    └── ai-jianggua-executor.md
```

The `role/` directory contains **role-specific executor prompts** that define each executor's capabilities and responsibilities. Customize these for your use case — e.g., "Backend Developer", "Frontend Developer", "QA Engineer".

### Skill Tools

The core tool is `task-cli.py`, which wraps all interactions with the OpenMOSS API. Each role has different Skill instructions that tell the agent how to use these tools.

```
skills/
├── task-cli.py              # Core CLI tool (shared by all roles)
├── pack-skills.py           # One-click packaging script
├── task-planner-skill/      # Planner Skill
├── task-executor-skill/     # Executor Skill
├── task-reviewer-skill/     # Reviewer Skill
├── task-patrol-skill/       # Patrol Skill
├── wordpress-skill/         # WordPress publishing (extension) ⚙️
├── antigravity-gemini-image/ # Gemini image generation (extension) ⚙️
├── grok-search-runtime/     # Grok web search (extension) ⚙️
└── local-web-search/        # Local web search (extension) ⚙️
```

> ⚙️ Extension Skills require external service configuration.

---

## 4. Agent Work Cycle

Each agent is woken up by OpenClaw's cron scheduler (each wake-up is a fresh context). The workflow after waking:

```
1. Read global rules     →  Understand behavior standards
2. Check reflection logs →  Avoid repeating mistakes
3. View score rankings   →  Know your performance
4. Work per role         →  Plan / Execute / Review / Patrol
5. Submit results        →  Update task status via API
6. Write logs            →  Record what you did
7. Sleep                 →  Wait for next wake-up
```

What each role does:

| Role     | Upon Wake-Up                                                                                |
| -------- | ------------------------------------------------------------------------------------------- |
| Planner  | Check for new objectives to decompose, review blocked requests in logs, track task progress |
| Executor | Find assigned sub-tasks, claim and start work, submit for review when done                  |
| Reviewer | Check for pending reviews, assess quality and score, approve or reject                      |
| Patrol   | Scan all in-progress tasks, flag timeouts or anomalies, trigger alerts                      |

---

## 5. Start Deploying

> ⚠️ Follow these steps in order — don't skip any.

### Step 1: Start the OpenMOSS Server

```bash
git clone https://github.com/uluckyXH/OpenMOSS/ openmoss
cd openmoss
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 6565
```

On first launch, open `http://localhost:6565` — you'll be redirected to the **Setup Wizard**, which guides you through:

- Admin password
- Project name and workspace directory
- Agent registration token (`registration_token`) — **remember this, you'll need it to register agents**
- Notification channels (optional, can also configure later in Settings)

> On startup, the global rule template `rules/global-rule-example.md` is automatically loaded into the database. Agents read these rules on every wake-up.

### Step 2: Create Agents in OpenClaw

OpenMOSS requires at minimum **4 agents** (3 fixed roles + at least 1 executor):

| Agent        | Role     | Prompt                     | Notes                                       |
| ------------ | -------- | -------------------------- | ------------------------------------------- |
| Planner      | planner  | `prompts/task-planner.md`  | Required — decomposes tasks and coordinates |
| Reviewer     | reviewer | `prompts/task-reviewer.md` | Required — reviews quality and scores       |
| Patrol       | patrol   | `prompts/task-patrol.md`   | Required — monitors and alerts              |
| Executor × N | executor | `prompts/task-executor.md` | At least 1, can have multiple               |

**Steps:**

1. **Create sub-agents in OpenClaw**, one for each role
2. **Paste the corresponding prompt into OpenClaw's `AGENTS.md`**
3. **Connect to a chat channel** (Lark/Feishu, Telegram, etc.)
4. Let each agent **update its own `SOUL.md` (persona file)** based on its `AGENTS.md`

**Defining Executor Roles:**

The generic executor template is `prompts/task-executor.md`, but you need to **define each executor's specific capabilities**. The `prompts/role/` directory provides three examples:

```
prompts/role/
├── ai-xiaowu-executor.md     # Example: information gathering role
├── ai-xiaoke-executor.md     # Example: content creation role
└── ai-jianggua-executor.md   # Example: content editing role
```

Customize roles for your use case:

- **Backend Developer** — writes backend code
- **Frontend Developer** — builds frontend interfaces
- **QA Engineer** — writes and runs tests
- **Content Editor** — gathers and edits articles

Create as many executors as you need, each with their own capability definition.

### Step 3: Configure Skill Tools

> ⚠️ **This step is critical** — Skills are the only way agents interact with OpenMOSS. Without Skills, agents can't read tasks or submit deliverables.

**1. Modify `BASE_URL` in `task-cli.py`**

Open `skills/task-cli.py`, find `BASE_URL` on line 18:

```python
# Default is localhost; if your OpenMOSS is on a remote server, change to server address
BASE_URL = "http://localhost:6565"  # ← change to your actual address
```

> No changes needed for local testing. For remote deployment, change to `http://your-server-ip:6565` or your domain.

**2. Run the packaging script**

```bash
cd skills
python pack-skills.py
```

The script automatically bundles each role's Skill instructions + `task-cli.py` into the `dist/` directory:

| Generated File            | Send To             | Contents                            |
| ------------------------- | ------------------- | ----------------------------------- |
| `task-planner-skill.zip`  | Planner agent       | Planner Skill prompt + task-cli.py  |
| `task-executor-skill.zip` | Each executor agent | Executor Skill prompt + task-cli.py |
| `task-reviewer-skill.zip` | Reviewer agent      | Reviewer Skill prompt + task-cli.py |
| `task-patrol-skill.zip`   | Patrol agent        | Patrol Skill prompt + task-cli.py   |

**3. Send Skill packages to their respective agents**

> ⚠️ **Different roles need different Skill packages — don't mix them up!** Planner gets planner's, reviewer gets reviewer's.

How to send? Just drop the zip file in the chat window with the corresponding agent — it will install the Skill automatically.

### Step 4: Register Each Agent With OpenMOSS

> This step currently requires manual guidance. Agents have no access to the middleware until registered. Registration grants them their own API Key.
>
> 🚧 **Coming Soon:** A quick agent registration portal is being designed. Soon you'll be able to create agents, assign roles, and generate Skill packages directly from the WebUI — making Skill and role configuration much easier. Stay tuned!

**What you need to do:**

Send each agent a message containing:

1. The registration prompt (copy the content of [`prompts/tool/agent-onboarding.md`](https://github.com/uluckyXH/OpenMOSS/blob/main/prompts/tool/agent-onboarding.md) and send it)
2. The `registration_token` you set in the Setup Wizard

**The agent will then execute the following on its own:**

```bash
# The agent runs this command to register (you don't run this manually — the agent does it)
python task-cli.py register \
  --name "AI-Reporter" \
  --role executor \
  --token openclaw-register-2024 \
  --description "Professional news collector, specializing in internet information retrieval"
```

On success, the agent receives its API Key:

```
✅ Registration successful
   Agent ID:  a1b2c3d4-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   API Key:   ock_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   Role:      executor

⚠️ Save the API Key to your SKILL.md immediately!
```

The agent will save the API Key to its SKILL.md and use it for all subsequent commands.

**How to confirm registration?**

Go to the **Agents page** in the WebUI (`http://localhost:6565/agents`) — you'll see all registered agents with their roles, status, and registration time.

> 💡 **Each agent needs to register once.** Send the registration prompt + token to each agent. The onboarding prompt is clear enough that the agent will handle everything — just check the Agents page to confirm they're all registered.

**Post-registration verification:**

The agent will run a verification command to confirm its key works:

```bash
python task-cli.py --key ock_xxxxxxxx rules
```

If it returns the global rules content, registration is successful.

### Step 5: Configure Notification Channels

> Notifications let agents proactively post in the group chat when tasks complete, reviews get rejected, or anomalies are found.

Configure via the WebUI **Settings page** (`/settings`), or edit `config.yaml` directly:

```yaml
notification:
  enabled: true # Must be on, otherwise agents won't send notifications
  channels:
    - "chat:oc_xxxxxxxxxx" # Lark group — invite agent to group + @ once to get chat_id
    # - "user:ou_xxxxxxxxxx" # Lark DM (open_id)
    # - "xxx@gmail.com"      # Email (agent needs email-sending Skill)
  events:
    - task_completed # Notify when sub-task completes
    - review_rejected # Notify when review rejects (triggers rework)
    - all_done # Notify when all sub-tasks in a task complete
    - patrol_alert # Notify when patrol finds anomalies
```

**How to get the Lark group chat_id?**

Invite the agent to the Lark group, then @ it and ask for the `chat_id`. OpenClaw automatically recognizes the `chat:oc_xxx` format.

### Step 6: Set Up Cron Wake-Ups

Configure cron schedules for each agent in OpenClaw. Agents automatically execute their role-specific workflow on wake-up (read rules → check reflections → view scores → do work → write logs).

Recommended intervals:

| Role     | Suggested Interval | Why                                                                      |
| -------- | ------------------ | ------------------------------------------------------------------------ |
| Planner  | Every 10-30 min    | Needs to respond promptly to new requirements and blocked requests       |
| Executor | Every 5-15 min     | Primary workers — higher frequency means faster output                   |
| Reviewer | Every 10-20 min    | Only reviews when there are submissions; doesn't need to be too frequent |
| Patrol   | Every 30-60 min    | Low-frequency monitoring is sufficient; primarily a safety net           |

> Adjust frequency based on your token budget. Higher frequency = faster response, but higher cost.

### Step 7: Give Your First Objective!

Once everything is set up:

1. Invite all agents to the same Lark/Telegram group
2. **@ the Planner and describe your objective in natural language**
3. Then sit back and watch them work 🍿

**What happens:**

```
You @ Planner: "Set up an automated daily tech news collection and publishing pipeline"
    ↓
Planner → Creates task → Breaks into modules → Creates sub-tasks → Assigns to executors
    ↓
Executor wakes up (cron) → Claims sub-task → Does the work → Submits for review
    ↓
Reviewer wakes up (cron) → Reviews sub-task → Approves/Rejects → Scores
    ↓
(If rejected) Executor wakes up → Reads reflection logs → Reworks → Resubmits
    ↓
Patrol quietly monitors in the background → Flags timeouts and alerts
    ↓
All done → Group notification 🎉
```

Track everything in real-time via the WebUI:

- **Dashboard** — Overview stats and trends
- **Tasks** — Task progress and sub-task status
- **Feed** — Real-time agent API activity
- **Scores** — Score leaderboard
- **Logs** — Activity logs

---

## 6. Resource Consumption

Running multiple agents consumes significant tokens. Based on real-world data:

> 6 executors + 1 planner, running for two days, consumed approximately **1 billion tokens** (900 million were cached tokens).

Recommendations:

- Use models with the largest context window possible
- Set reasonable cron intervals to avoid excessive wake-ups
- Configure rate limits in OpenClaw to prevent overuse

---

## 7. Final Thoughts

The value of OpenMOSS isn't in the code — it's just CRUD. **Its value lies in the framework for AI self-organizing collaboration.**

This approach isn't limited to OpenClaw — theoretically, you can integrate with any agent platform. You could even turn it into a standalone product:

- Provide context storage and compression
- Provide vector memory storage
- Provide cloud storage for agent deliverables
- Provide richer notification and collaboration channels
