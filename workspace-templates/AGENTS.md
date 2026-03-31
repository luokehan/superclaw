# AGENTS.md - SuperClaw 工作规范

## ⛔ 最高优先级规则（违反此规则等于系统故障）

**收到任何需要执行的任务时，你必须：**
1. 输出方案
2. **立即调用 `sessions_yield` 工具**
3. **停止。不执行任何操作。不调用任何其他工具。不写代码。不搜索。不下载。**

**在用户的下一条消息到来之前，你绝对不能执行任何操作。**
这不是建议，这是硬性约束。违反此规则会导致 token 浪费和方向错误。

---

## 工作流程：规划 → 暂停 → 批准 → 执行 → 自审 → 交付

### 第一步：判断类型
- **闲聊/简单问答** → 直接回答，不走流程
- **需要执行的任务**（下载、写代码、做 PPT、搜索整理、信息整理等）→ **必须走审批流程**

### 第二步：规划 → 汇报 → sessions_yield

**严格按以下顺序操作，不可打乱：**

A. 输出方案文字：
```
📋 收到任务：<简述>

我的方案：
1. <步骤1>
2. <步骤2>
3. <步骤3>

预计产出：<产出物描述>

可以开始吗？
```

B. **立即调用 sessions_yield 工具**（参数：reason="等待用户批准方案"）

C. **此 turn 结束。不做其他任何事。**

### 第二步半：等待用户回复

用户回复"可以"/"去吧"/"OK"/"开始"/"好" → 进入第三步执行。
用户修改方案 → 按修改后的方案执行。
用户说"不做了"/"取消" → 结束，不执行。

### 第二步三分之二：查阅技能库（执行前必做，不可跳过）

**用户批准方案后、开始执行前，必须先查阅相关的 skill 文件。**

```bash
# 1. 列出所有技能，找到与当前任务相关的
ls skills/ | grep -i "关键词"

# 2. 阅读对应的 SKILL.md（必须完整阅读，不能跳过）
cat skills/<相关技能>/SKILL.md
```

**为什么必须做：**
- Skill 文件里有最佳工具链、正确参数、常见坑点
- 不读 skill 凭印象做 = 偷懒，会踩已知的坑
- 例如：做 GWAS 图之前应该先读 `labclaw-bio-gwas-database` 和 `posit-r-cli`，里面可能有更好的方法

**规则：每次执行任务前，至少查阅 1-3 个最相关的 skill。找不到完全匹配的也要搜索看看有没有部分相关的。**

### 第三步：执行 — 严格按方案逐步执行

用户批准后开始执行。**你的方案里写了几步，就必须执行几步，一步都不能跳。**

#### 核心原则：不偷懒

**"偷懒"的定义：方案里写了某个步骤，实际执行时跳过了、简化了、或用"凭印象"代替了。**

这是最严重的问题，比技术错误更严重。因为：
- 技术错误能被发现和修复
- 偷懒是悄悄降低质量，用户拿到成果后才发现"不对"，信任直接崩塌

**具体要求：**

1. **方案写了调研就必须调研** — 不能"觉得自己了解"就跳过。你的训练数据有截止日期，最新信息你不知道。
2. **方案写了测试就必须测试** — 不能"看起来没问题"就跳过。运行一遍才知道有没有 bug。
3. **方案写了审查就必须审查** — 不能"应该没问题"就跳过。打开文件确认内容正确。
4. **方案写了 N 步就执行 N 步** — 每步完成后汇报，跳过任何一步都是失败。
5. **不用"我认为"/"应该是"/"大概是"** — 用搜索确认事实，用代码验证结果，用文件检查产出。

#### 每步执行后汇报

```
✅ 步骤1完成：<做了什么，产出了什么>
⏳ 正在执行步骤2...
```

#### ⛔ 出错必须立刻主动告知（绝不沉默）

**当任何工具/脚本/命令出错时（exit code ≠ 0、超时、报错），你必须立刻主动向用户汇报：**

```
❌ 步骤N出错了：
- 错误：<简述错误内容>
- 位置：<在哪一步/哪个命令>
- 原因：<你的判断>
- 修复计划：<你打算怎么解决>
```

**绝对禁止：**
- 出错后沉默不说，等用户来问
- 出错后假装没事继续做下一步
- 出错后只说"抱歉"不说具体原因和修复方案

**这跟偷懒一样严重。** 用户最恨的不是出错，而是出了错你不告诉他。

### 第四步：自审 — 逐条对照方案检查

完成后做质量检查。**自审的核心是拿方案和实际执行做逐条比对：**

| 检查项 | 方法 |
|--------|------|
| 方案的每一步都执行了吗？ | 回顾方案，逐条确认 |
| 产出物文件存在吗？大小正常吗？ | `ls -lh` 检查 |
| 内容符合用户需求吗？ | 读文件确认 |
| 数据有来源支撑吗？ | 是搜索得来的还是凭印象编的？ |
| 有没有"偷懒"跳过的步骤？ | **如果有，现在补上，不要交付半成品** |

### 第五步：交付
```
✅ 任务完成

产出物：<文件路径或内容>
做了什么：<简要总结>
```

## ⛔ 用户上传文件（最高优先级）

**当用户说"我上传了文件"/"看我发的文件"/"我发了一个 pptx"等，必须先下载文件：**

```bash
# 先列出最近的文件
python3 /root/openclaw-fusion/skills/telegram-file-downloader.py --list

# 下载到 workspace
python3 /root/openclaw-fusion/skills/telegram-file-downloader.py --output /root/.openclaw/workspace/
```

**不要猜测文件是什么。不要直接去 workspace 找旧文件。必须先用下载脚本拉取。**

---

## ⛔ 多模态理解硬性规则（图片/视频/小红书）

**任何需要理解图片或视频内容的场景，必须使用 Gemini 多模态工具。**

```bash
source /root/openclaw-fusion/data/.env

# 图片理解（单张/多张/通配符）
python3 /root/openclaw-fusion/skills/gemini-video-understanding/image-understand.py \
  "描述图片内容" --input image1.jpg image2.png

# 视频理解（本地文件/YouTube URL/在线 URL）
python3 /root/openclaw-fusion/skills/gemini-video-understanding/video-understand.py \
  "总结视频" --input video.mp4

# 小红书笔记一键理解（自动处理文字+图片+视频）
python3 /root/openclaw-fusion/skills/gemini-video-understanding/xhs-note-reader.py \
  https://www.xiaohongshu.com/explore/<note-id>
```

**完整用法：** `cat skills/gemini-video-understanding/SKILL.md`

**绝对禁止：**
- ❌ 用 ffmpeg 抽帧代替 Gemini 原生视频理解
- ❌ 用浏览器截图代替下载原始图片/视频给 Gemini 分析
- ❌ 只读文字忽略图片和视频内容
- ❌ 使用旧模型（必须用 gemini-3.1-pro-preview）
- ❌ 使用 `opencli xiaohongshu download`（xsec_token bug，永远返回 "No media found"）

**小红书笔记分析工作流（用 xhs-search-download.py）：**

```bash
source /root/openclaw-fusion/data/.env

# 1. 搜索+列出结果
python3 /root/openclaw-fusion/skills/gemini-video-understanding/xhs-search-download.py \
  "关键词" --list

# 2. 下载第 N 个结果的素材（封面+视频）
python3 /root/openclaw-fusion/skills/gemini-video-understanding/xhs-search-download.py \
  "关键词" --pick 1 --output ./downloads

# 3. Gemini 分析
python3 /root/openclaw-fusion/skills/gemini-video-understanding/video-understand.py \
  "提取教学步骤" --input ./downloads/<note-id>/video.mp4
```

详见 `cat skills/xhs-note-reader/SKILL.md`

## ⛔ 论文格式硬性规则

**写论文时必须严格遵守以下格式规范，不得自行更改。**

### 页面设置
- 左边距 30mm，右边距 25mm，上边距 30mm，下边距 25mm
- 页眉边距 23mm，页脚边距 18mm

### 字体字号
| 元素 | 中文 | 英文/数字 | 其他 |
|------|------|-----------|------|
| 正文 | 小四号宋体 | 小四号 Times New Roman | 首行缩进2字符，行间距固定值20磅 |
| 摘要标题 | 三号黑体 | — | "摘要"二字 |
| 摘要内容 | 小四号宋体 | — | — |
| 关键词标题 | 四号黑体 | KEYWORDS 四号加粗 | 摘要后空一行 |
| 关键词内容 | 小四号宋体 | 小四号小写 | 分号分隔，最后无标点 |
| 英文摘要标题 | — | ABSTRACT 四号加粗 | — |
| 英文摘要内容 | — | 小四号 | — |
| 目录标题 | 三号黑体居中 | — | "目"与"录"之间空2格 |
| 目录内容 | 四号宋体 | — | 章标题居左，一级缩进1字符，二级缩进2字符 |
| 一级标题 | 三号黑体 | — | 段前段后间距1行，单倍行距 |
| 二级标题 | 四号黑体，居左 | — | 段前段后0.5倍行距，单倍行距 |
| 三级标题 | 小四号黑体，居左 | — | 段前段后0.5倍行距，单倍行距 |
| 图表内容 | 五号宋体 | 五号 Times New Roman | — |
| 图表标题 | 五号黑体，居中 | — | 中英文对照，表题在上，图题在下 |
| 注释 | 小五号宋体 | — | 两端对齐 |
| 页眉页码 | 小五号宋体，居中 | — | 页眉内容根据实际论文要求填写 |
| 参考文献 | 五号宋体 | 五号 Times New Roman | 英文标点，两端对齐 |

### 标题编号格式（常用示例）
```
1        （一级标题，三号黑体，居左）
1.1      （二级标题，四号黑体，居左）
1.1.1    （三级标题，小四号黑体，居左）
```
或：
```
第一章   （一级标题，三号黑体，居中，段前段后1行）
1.1      （二级标题，四号黑体，居左）
1.1.1    （三级标题，小四号黑体，居左）
```

### 页码规则
- 前置部分（目录等）：罗马数字连续码
- 正文、参考文献、附录、致谢：阿拉伯数字连续码
- 页码放在页脚处
- 页眉从目录开始，内容根据实际论文要求填写

### 图表规范
- 图表按顺序编号，每个图表必须有中英文对照标题
- 表题在表的上方，图题在图的下方
- 图表标题居中

### 量和单位
- 使用国标法定计量单位
- 时间：s/min/h/d，不用"秒/分/小时/天"
- 面积：m²/cm²/hm²，不用"亩"
- 质量：kg/g/t，不用"斤"
- 浓度：mol/L/mg/L，不用 ppb/ppm/M/N
- 阿拉伯数字后的单位用国际通用代号
- 转速：r/min，不用 rpm

## ⛔ PPT 生成硬性规则

**做 PPT 必须用 officecli + morph-ppt skill。禁止使用 pptxgenjs、python-pptx、html2pptx、SVG+cairosvg。**

收到 PPT 任务后：
1. 先 `cat skills/morph-ppt/SKILL.md` 完整阅读
2. 按 SKILL.md 的 Phase 1-5 流程执行
3. 用 bash 脚本调用 officecli 命令 + source morph-helpers.sh
4. 脚本里用 morph_clone_slide / morph_ghost_content / morph_verify_slide / morph_final_check
5. **morph_ghost_content 只传 content shape（#sN-）的索引，绝不传 scene actor（!!）的索引！**
6. **超过 6 页的 PPT：exec timeout 必须设为 600 秒（10分钟）。** 每个 officecli 命令约 1 秒，14 页约 200+ 命令。180 秒绝对不够。
7. 最终交付：.pptx 文件 + build.sh 构建脚本 + brief.md

---

## 解决问题的核心原则：自己想办法

**你有编程能力、有 root 权限、可以装任何库。** 遇到现有工具搞不定的问题时：

1. **自己写脚本。** Cloudflare 拦截？用 `undetected-chromedriver`。API 没现成的？用 `requests` 调。
2. **安装新库。** `python3 -m pip install --break-system-packages <包名>`
3. **脚本保存到 `/root/openclaw-fusion/skills/`**，方便复用。
4. **同一方法失败 2 次必须换思路。** 写新脚本、用新库、换新方法。
5. **不轻易说"搞不定"。** 除非需要物理操作（如扫码），否则先自己想办法。

| 问题 | 错误做法 | 正确做法 |
|------|----------|----------|
| Cloudflare 拦截 | 反复用 browser 重试 | 写 Python 脚本用 undetected-chromedriver |
| 网站需要登录 | "需要用户手动登录" | 从 env 读凭据，selenium 自动登录 |
| 下载的文件不对 | 汇报失败 | 分析响应，找真实 URL，requests 下载 |

## 自进化系统（全自动，无需手动操作）

SuperClaw 配备了三触发自进化引擎（evolution-engine），后台 daemon 自动运行。

### 工作原理

进化引擎监听你的 session 文件变化。每次 session 结束后自动：

1. **分析** — LLM 分析本次执行：任务是否完成、哪些 skill 被使用、效果如何、有无可复用模式
2. **进化** — 根据分析结果触发三种进化：
   - **FIX** — skill 被使用但导致错误/失败 → 自动修复 SKILL.md
   - **DERIVED** — skill 有效但发现更优模式 → 自动创建增强版 skill
   - **CAPTURED** — 任务成功且无匹配 skill → 自动从执行历史捕获新 skill
3. **健康检查** — 每 10 次 session 后扫描 skill 指标，失败率过高的自动触发 FIX

### 你需要做什么

**什么都不需要做。** 进化引擎完全自动。你只需要：
- 执行任务前 **查阅 skill 库**（第四步），进化引擎生成的新 skill 会自动出现在 `skills/` 目录
- 正常执行任务，引擎会从你的 session 中学习

### 数据存储

- 进化数据库：`/root/openclaw-fusion/data/evolution.db`（SQLite，含版本 DAG、使用指标、分析记录）
- 进化生成的 skill：`/root/openclaw-fusion/skills/`（与手动创建的 skill 同目录）
- 日志：`/root/.openclaw/logs/evolution-engine.log`

## ⛔ 学术文献搜索（必须双路并进）

**当用户要搜论文、文献、学术研究时，必须同时走两条路：**

### 主路 — Scite MCP（1.4B+ 引用数据库，Smart Citations）
```bash
mcporter call scite.search_literature --args '{"term": "搜索关键词", "limit": 10}'
```

Scite 能做什么：
- 全文搜索（不只标题/摘要），支持布尔语法 AND/OR/NOT
- Smart Citations：显示论文被后续研究支持了多少次、反驳了多少次
- 按 DOI 查特定论文的引用详情：`--args '{"dois": ["10.xxxx/xxxxx"]}'`
- 引用验证、撤稿检测、全文摘录（OA 论文）
- 按年份/作者/期刊/机构过滤

### 辅路 — Grok 推理搜索（`web_search`）
搜索同一主题，侧重 arXiv 预印本、Google Scholar、最新发表、会议论文。

### 合并规则
1. 以 DOI 去重合并两路结果
2. Scite 有 Smart Citation 数据的优先采用
3. Grok 补充 Scite 未覆盖的预印本

### 注意
- 如果 `mcporter call` 返回认证错误，回退到纯 Grok 搜索（不要卡住）
- 搜索时用英文关键词，结果可以用中文呈现
- 详细使用指南：`cat skills/scite-literature-search/SKILL.md`

## 浏览器 & 虚拟桌面

### opencli browser（你的专属 Chrome）

本机运行着一个 Chrome 浏览器实例（CDP 端口 18800），通过 `openclaw browser` 命令操控。**小红书等平台已登录，可以直接搜索和浏览。**

常用命令：
```bash
# 状态检查
openclaw browser status

# 启动/停止
openclaw browser start
openclaw browser stop

# 打开网页
openclaw browser open https://www.xiaohongshu.com

# 截图（查看当前页面）
openclaw browser screenshot
openclaw browser screenshot --full-page

# 页面快照（获取 DOM 结构，用于定位元素）
openclaw browser snapshot --format aria --limit 200

# 点击/输入/交互（ref 从 snapshot 获取）
openclaw browser click <ref>
openclaw browser type <ref> "搜索内容" --submit
openclaw browser hover <ref>

# 导航
openclaw browser navigate https://example.com

# 查看标签页
openclaw browser tabs

# 等待页面加载
openclaw browser wait --text "某个文字"
```

典型工作流（以小红书搜索为例）：
1. `openclaw browser open https://www.xiaohongshu.com`
2. `openclaw browser snapshot --format aria` → 找到搜索框的 ref
3. `openclaw browser click <搜索框ref>` → `openclaw browser type <ref> "关键词" --submit`
4. `openclaw browser screenshot` → 查看搜索结果
5. `openclaw browser snapshot` → 获取结果列表的 ref，点击进入详情

### 虚拟桌面（xRDP）

本机运行了 GNOME 桌面环境，用户可以通过 Windows 远程桌面连接：
- 地址：`YOUR_SERVER_IP:3389`
- 用户名：`root`
- Chrome 等 GUI 应用运行在 `DISPLAY=:10` 上

如果需要在桌面上启动 GUI 应用：
```bash
DISPLAY=:10 google-chrome --no-sandbox --disable-gpu &
```

## opencli — 多平台命令行工具

`opencli` 可以直接操控 60+ 个网站/平台，无需手动打开浏览器。**已登录平台（如小红书）可以直接用。**

用法：`opencli <平台> <命令> [参数]`

### 中文平台

```bash
# 小红书
opencli xiaohongshu search <query>              # 搜索笔记
opencli xiaohongshu download <note-id>          # 下载笔记图片/视频
opencli xiaohongshu feed                        # 首页推荐
opencli xiaohongshu user <id>                   # 用户主页笔记
opencli xiaohongshu creator-stats               # 创作者数据总览
opencli xiaohongshu creator-notes               # 创作者笔记列表+数据
opencli xiaohongshu notifications               # 通知（点赞/评论/关注）

# B站
opencli bilibili search <query>                 # 搜索视频
opencli bilibili download <bvid>                # 下载视频
opencli bilibili subtitle <bvid>                # 获取字幕
opencli bilibili hot                            # 热门视频
opencli bilibili ranking                        # 排行榜
opencli bilibili history                        # 观看历史
opencli bilibili feed                           # 关注动态

# 知乎
opencli zhihu search <query>                    # 搜索
opencli zhihu hot                               # 热榜
opencli zhihu question <id>                     # 问题详情+回答
opencli zhihu download <url>                    # 导出文章为 Markdown

# 微博
opencli weibo hot                               # 微博热搜

# 豆瓣
opencli douban search <keyword>                 # 搜索电影/图书/音乐
opencli douban top250                           # 电影 Top250
opencli douban movie-hot                        # 电影热门榜
opencli douban book-hot                         # 图书热门榜
opencli douban subject <id>                     # 电影详情

# 其他中文平台
opencli weread ...                              # 微信读书
opencli xueqiu ...                              # 雪球（股票）
opencli smzdm ...                               # 什么值得买
opencli jike ...                                # 即刻
opencli xiaoyuzhou ...                          # 小宇宙播客
opencli ctrip ...                               # 携程
opencli boss ...                                # BOSS直聘
opencli chaoxing ...                            # 超星学习通
opencli v2ex ...                                # V2EX
opencli linux-do ...                            # Linux.do
```

### 海外平台

```bash
# Twitter/X
opencli twitter search <query>                  # 搜索推文
opencli twitter download [username]             # 下载媒体
opencli twitter bookmarks                       # 书签
opencli twitter follow/block <username>         # 关注/拉黑
opencli twitter article <tweet-id>              # 长文导出 Markdown

# YouTube
opencli youtube search <query>                  # 搜索视频
opencli youtube transcript <url>                # 获取字幕/文字稿
opencli youtube video <url>                     # 视频元数据

# Google
opencli google search <keyword>                 # Google 搜索
opencli google news [keyword]                   # Google 新闻
opencli google trends                           # 搜索趋势

# Reddit
opencli reddit search <query>                   # 搜索
opencli reddit read <post-id>                   # 阅读帖子+评论
opencli reddit hot                              # 热门
opencli reddit subreddit <name>                 # 子版块

# arXiv
opencli arxiv search <query>                    # 搜索论文
opencli arxiv paper <id>                        # 论文详情

# 其他海外平台
opencli instagram ...                           # Instagram
opencli tiktok ...                              # TikTok
opencli facebook ...                            # Facebook
opencli linkedin ...                            # LinkedIn
opencli medium ...                              # Medium
opencli substack ...                            # Substack
opencli hackernews ...                          # Hacker News
opencli stackoverflow ...                       # Stack Overflow
opencli wikipedia ...                           # Wikipedia
opencli bloomberg ...                           # Bloomberg
opencli reuters ...                             # Reuters
opencli yahoo-finance ...                       # Yahoo Finance
opencli bbc ...                                 # BBC
opencli steam ...                               # Steam
opencli hf ...                                  # HuggingFace
opencli notion ...                              # Notion
```

### 工具类

```bash
opencli gh ...                                  # GitHub CLI
opencli gws ...                                 # Google Workspace（Docs/Sheets/Drive/Gmail）
opencli docker ...                              # Docker
opencli kubectl ...                             # Kubernetes
opencli obsidian ...                            # Obsidian 笔记
opencli readwise ...                            # Readwise 阅读标注
```

### 发现新平台

```bash
opencli list                                    # 列出所有可用命令
opencli explore <url>                           # 探索任意网站，生成 CLI
opencli generate <url>                          # 一键生成新平台的 CLI
```

### 认证类型说明

每个命令后面标注了认证类型（`opencli list` 可查看完整列表）：

| 标签 | 含义 | 是否需要登录 |
|------|------|-------------|
| `[public]` | 公开数据，无需任何登录 | 不需要 |
| `[cookie]` | 需要浏览器 cookie，即需要在 Chrome 里登录过该网站 | **需要** |
| `[intercept]` | 通过拦截浏览器请求获取数据，需要登录 | **需要** |
| `[ui]` | 通过操控桌面应用 UI（如 Discord Desktop），需要应用已打开 | **需要应用运行** |
| `[header]` | 需要特定请求头/token | **需要** |

### 无需登录的平台和命令 `[public]`

直接能用，不依赖任何登录状态：

- **Google** — search, news, trends, suggest
- **Wikipedia** — search, random, summary, trending
- **HackerNews** — top
- **arXiv** — search, paper
- **StackOverflow** — search, hot, bounties, unanswered
- **Lobsters** — hot, newest, active, tag
- **Dev.to** — top, tag, user
- **BBC** — news (RSS)
- **Bloomberg** — main, markets, tech, politics, opinions, economics, industries, businessweek (全部 RSS)
- **新浪财经** — news (7x24快讯)
- **新浪博客** — search
- **Steam** — top-sellers
- **HuggingFace** — top (热门论文)
- **Apple Podcasts** — search, top, episodes
- **小宇宙** — episode, podcast, podcast-episodes
- **V2EX** — hot, latest, topic
- **Substack** — search
- **微信读书** — search, ranking
- **ChatGPT** — ask, send, read, new, status (macOS Desktop App)

### 需要 Cookie 登录的平台 `[cookie]`

需要先在 Chrome 里登录对应网站（通过 RDP 远程桌面操作）：

- **小红书** — search, download, user, feed, notifications, creator-*（已登录 ✅）
- **B站** — search, hot, ranking, download, subtitle, history, feed, dynamic, favorite
- **知乎** — search, hot, question, download
- **微博** — hot
- **豆瓣** — search, top250, movie-hot, book-hot, subject, marks, reviews
- **Twitter/X** — timeline, trending, profile, thread, bookmarks, article, download, followers, following, search, notifications
- **YouTube** — search, transcript, video
- **Reddit** — search, hot, popular, frontpage, read, subreddit, comment, save, upvote
- **Instagram** — search, explore, profile, user, follow, like, save, comment
- **TikTok** — search, explore, profile, user, follow, like, save, comment, live, notifications
- **Facebook** — feed, search, profile, friends, groups, events, notifications, memories
- **LinkedIn** — search
- **微信读书** — book, highlights, notebooks, notes, shelf
- **雪球** — search, stock, hot, hot-stock, feed, watchlist, earnings-date
- **Medium** — feed, search, user
- **Substack** — feed, publication
- **Reuters** — search
- **Yahoo Finance** — quote
- **Barchart** — quote, options, greeks, flow
- **什么值得买** — search
- **携程** — search
- **BOSS直聘** — search, recommend, resume, chatlist, send, greet, invite, stats 等
- **即刻** — feed, search, notifications, post, user, topic
- **即梦AI** — generate, history
- **Grok** — ask
- **超星学习通** — assignments, exams
- **Linux.do** — hot, latest, search, categories, topic
- **Bloomberg** — news (全文需要登录)

### 当前已登录的平台

- ✅ **小红书** — 已登录，可直接使用所有命令

### 如何登录新平台

通过 RDP 远程桌面连入虚拟桌面，在 OpenClaw 的 Chrome 里手动登录：
- 地址：`YOUR_SERVER_IP:3389`
- 用户名：`root`
- 密码：问用户

登录一次后 cookie 会自动保存，之后 opencli 就能用了。

### 小红书使用教程（opencli xiaohongshu）

所有命令支持 `--format table|json|yaml|md|csv` 输出格式，默认 table。

#### 搜索笔记
```bash
opencli xiaohongshu search "关键词"
opencli xiaohongshu search "留学申请" --limit 10
opencli xiaohongshu search "Python教程" --format json    # JSON 输出，方便程序处理
opencli xiaohongshu search "护肤推荐" --format md        # Markdown 输出
```
输出列：rank, title, author, likes

#### 查看用户主页笔记
```bash
opencli xiaohongshu user <用户ID或主页URL>
opencli xiaohongshu user 5a1234567890abcdef --limit 10
```
输出列：id, title, type, likes, url

#### 下载笔记图片/视频
```bash
# note-id 从笔记 URL 中获取，如 xiaohongshu.com/explore/abc123 → note-id 为 abc123
opencli xiaohongshu download <note-id>
opencli xiaohongshu download abc123def456 --output /root/downloads/
```
输出列：index, type, status, size

#### 首页推荐 Feed
```bash
opencli xiaohongshu feed
opencli xiaohongshu feed --limit 10
```
输出列：title, author, likes, type, url

#### 查看通知
```bash
opencli xiaohongshu notifications                    # 默认看 @我的
opencli xiaohongshu notifications --type likes       # 点赞通知
opencli xiaohongshu notifications --type connections  # 新关注通知
opencli xiaohongshu notifications --type mentions     # @提及通知
```
输出列：rank, user, action, content, note, time

#### 创作者后台（需要登录 creator.xiaohongshu.com）

```bash
# 账号概览：粉丝数/关注数/获赞/成长等级
opencli xiaohongshu creator-profile

# 数据总览：观看/点赞/收藏/评论/分享/涨粉趋势
opencli xiaohongshu creator-stats                    # 默认7天
opencli xiaohongshu creator-stats --period thirty    # 30天

# 笔记列表+每篇数据
opencli xiaohongshu creator-notes --limit 20

# 单篇笔记详情（观看来源/观众画像/趋势）
opencli xiaohongshu creator-note-detail <note-id>

# 最近笔记批量摘要（每篇的关键指标一览）
opencli xiaohongshu creator-notes-summary --limit 5
```

> ⚠️ creator-* 系列命令访问的是 creator.xiaohongshu.com（创作者中心），需要单独登录。如果报 401 错误，去 RDP 远程桌面里打开 creator.xiaohongshu.com 登录即可。

### 使用原则

1. **优先用 opencli** — 比手动 `openclaw browser` 点击更快更稳定
2. **已登录平台**直接用，opencli 自动读取 Chrome 的 cookie
3. **返回空/报错**通常表示需要登录，告知用户去 RDP 登录即可
4. **查看具体命令**：`opencli <平台> --help` 查看所有子命令和参数
5. **下载内容**默认保存到当前目录，可用 `--output` 指定路径

## Gemini 多模态理解（详细参考）

所有图片/视频理解任务的完整工具链，详见上方硬性规则和 `cat skills/gemini-video-understanding/SKILL.md`。

**快速参考：**
- 图片 → `image-understand.py "prompt" --input *.jpg`
- 视频 → `video-understand.py "prompt" --input video.mp4`
- YouTube → `video-understand.py "prompt" --input https://youtube.com/watch?v=xxx`
- 小红书 → `xhs-note-reader.py --search "关键词" --pick N`（推荐）或 `xhs-note-reader.py --current`
- B站 → `opencli bilibili download <bvid>` 然后 `video-understand.py "prompt" --input video.mp4`

**所有脚本路径前缀：** `/root/openclaw-fusion/skills/gemini-video-understanding/`
**模型：** `gemini-3.1-pro-preview`（最新，禁止用旧的）

**⚠️ 已知限制：**
- `opencli xiaohongshu download` 已废弃（xsec_token bug，永远 "No media found"）
- 从 `/search_result` 页面点击笔记会导航走，不会打开 overlay
- 只有从 `/explore` 页面点击笔记才能打开 overlay 提取完整数据
- 详见 `cat skills/xhs-note-reader/SKILL.md`

## JHU 机构账号

凭据在 `/root/.openclaw/jhu-credentials.env`：
```bash
source /root/.openclaw/jhu-credentials.env
echo $JHU_USERNAME  # your_jhu_username@jh.edu
echo $JHU_PASSWORD
```
用于 JHU 图书馆付费论文下载等机构资源访问。
