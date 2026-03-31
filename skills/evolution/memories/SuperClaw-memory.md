# SuperClaw 经验记忆

> 此文件由系统自动维护。Agent 每次唤醒时读取，任务完成后写入。


# SuperClaw 经验记忆

> 此文件由系统自动维护。Agent 每次唤醒时读取，任务完成后写入。


### [工具用法] 2026-03-24 08:56

matplotlib中文字体配置方法：import matplotlib.font_manager as fm; fm.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'); prop=fm.FontProperties(fname=...); matplotlib.rcParams['font.family']=[prop.get_name(),'DejaVu Sans']; rcParams['axes.unicode_minus']=False。需在plt使用前配置。

### [任务模式] 2026-03-24 08:56

高质量PPT设计原则：1)颜色体系：深色背景(#080C14)+主accent色+辅助色，最多3种accent；2)每页左侧窄条做品牌色边框，标题下方细线做装饰；3)数据卡片：深色背景+彩色边框+大字数值+小字描述；4)图表用matplotlib生成PNG嵌入，比pptx原生图表更灵活；5)16:9宽屏(13.33×7.5英寸)；6)封面/结尾页视觉最强，中间页保持一致语言。

### [任务模式] 2026-03-24 10:43

任务：黄金实时价格及趋势查询。方法：用web_search同步搜索中英文关键词，中文搜国内金价，英文搜国际分析师预测，两路并行效率高。踩坑：无。改进：此类行情查询，并行双语搜索是最优解，结构化表格输出比纯文字更清晰

### [审查反馈] 2026-03-24 11:32

【重要教训】不能跳过调研步骤。水产养殖 PPT 任务中偷懒跳过调研直接凭印象写内容，结果内容缺乏数据支撑，用户不满意。根本原因：觉得自己了解话题就不搜索了。正确做法：任何内容创作任务（PPT/报告/文案）的第一步永远是 web_search 搜最新真实数据，然后基于数据写内容。哪怕自己很了解也要搜——因为训练数据有截止日期，最新数字不知道。

### [流程优化] 2026-03-24 11:34

【核心教训】不偷懒。方案写了几步就执行几步，不跳过任何一步。具体表现：不用'凭印象'代替搜索（数据可能过时或错误），不用'看起来对'代替运行测试（可能有隐藏bug），不用'应该没问题'代替打开文件检查（可能乱码/缺内容）。自审时拿方案逐条对照实际执行，缺了就补。偷懒比技术错误更严重——技术错误能被发现，偷懒是悄悄降质量。

### [工具用法] 2026-03-24 14:04

PPT生成：不再用 ppt-agent（SVG+HTML，不产出.pptx）。改用 morph-ppt + officecli。officecli 是独立CLI工具直接操作.pptx，morph-ppt skill提供Morph动画工作流。52种预设风格在 skills/morph-ppt/reference/styles/INDEX.md。必须用 morph-helpers.sh 辅助函数（自动验证转场和ghost）。Shape命名：scene actors用!!前缀，content用#sN-前缀。每页必须transition=morph。

### [错误修复] 2026-03-24 14:04

PPT旧方案废弃：ppt-generator-skill/ppt-agents/ppt-shared/ppt-gemini-cli 全部删除。不要再用cairosvg+python-pptx拼接方案，不要生成SVG幻灯片。直接用officecli命令行生成.pptx。参考 skills/morph-ppt/SKILL.md。

### [错误修复] 2026-03-24 16:03

PPT构建脚本两大坑：1) morph_ghost_content 只能传 content shape（#sN-前缀）的索引号，不能传 scene actor（!!前缀）的索引号。ghost 前先用 officecli get 看哪些是 scene actor 哪些是 content。2) 超过6页PPT的脚本需要设 exec timeout=300，因为每个 officecli 命令约1秒，14页约200秒。3) set -e 会让 verify 失败时终止整个脚本，可以用 morph_verify_slide ... || true 防止中断。

### [审查反馈] 2026-03-24 16:04

最重要的教训：任何工具/脚本报错时必须立刻主动告诉用户。不能沉默等用户追问。用户来问'怎么了'说明你已经犯了错。出错后的正确做法：立刻汇报错误内容+位置+原因+修复方案。

### [错误修复] 2026-03-24 16:07

PPT exec timeout：14页PPT需要200+个officecli命令，每个约1秒。timeout必须设600秒（10分钟）。180秒会导致只跑到第9页就被kill。之前设的300也不够保险。记住：页数×15（命令数/页）= 最低秒数，再加50%余量。
