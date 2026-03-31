---
name: propose_and_confirm_action
description: A pattern to propose a detailed plan of action to the user using `sessions_yield` and await their explicit approval before proceeding with potentially impactful or resource-intensive tasks, ensuring user consent and transparency.
version: 1.0
evolved_from:
evolution_type: CAPTURED
---

# 提议并确认行动

## 适用场景
当任务涉及以下情况时，应使用此 Skill：
- 任务包含多个复杂步骤，需要用户理解和同意执行路径。
- 任务可能消耗大量资源（例如，广泛的网页搜索、API 调用产生费用、长时间的计算）。
- 任务可能对用户环境产生潜在影响或副作用（例如，修改文件、部署代码、执行系统命令）。
- 在执行不可逆或难以撤销的操作之前。
- 示例：生成复杂报告、执行数据分析、自动化部署流程、进行系统配置更改。

## 步骤
1.  **分析任务并制定详细计划**：仔细分析用户请求，将其分解为清晰、可执行的逻辑步骤。考虑潜在的风险、所需资源、预期结果以及替代方案。
2.  **构建清晰的行动提议**：将制定的计划整理成一份易于理解的文本。明确说明将要执行的每个主要步骤、使用的工具、预期达成的目标以及任何重要的假设或限制。
3.  **使用 `sessions_yield` 提议并等待确认**：通过 `sessions_yield` 将详细计划展示给用户，并明确请求他们的确认。
4.  **处理用户响应**：
    *   如果用户明确同意（例如，回复 "yes"），则继续执行计划。
    *   如果用户拒绝（例如，回复 "no"）或要求修改，则根据反馈调整计划，或寻求进一步的澄清。
    *   如果用户响应不明确，则进一步提问以获取清晰的指示。
5.  **执行或重新规划**：根据用户确认结果，执行已批准的计划；如果计划被拒绝或需要修改，则重新规划并可能再次提议。

## 工具和命令
-   **`sessions_yield`**: 用于向用户展示信息并等待其响应。

    *   **语法**: `sessions_yield(content: str, require_confirmation: bool = False, type: str = "text") -> Union[bool, str]`
    *   **`content`**: 这是一个字符串，包含你希望向用户展示的详细计划。强烈建议使用 Markdown 格式使其更易读，例如使用列表、粗体等。
    *   **`require_confirmation=True`**: 这个参数至关重要。当设置为 `True` 时，`sessions_yield` 会暂停执行，等待用户明确的 "yes" 或 "no" 响应。
    *   **返回值**: 当 `require_confirmation=True` 时，`sessions_yield` 通常会返回一个布尔值 (`True` 表示确认，`False` 表示拒绝)。如果用户输入了其他内容，系统可能会尝试解析或返回原始输入。

**示例用法**:

```python
# 假设用户请求：搜索最新的 GPT-5 消息，整理成一份简报

# 1. 制定计划
plan = """
好的，我将为您搜索最新的 GPT-5 消息并整理成一份简报。我计划执行以下步骤：

1.  **使用 `web_search` 搜索**：
    *   搜索关键词："GPT-5 latest news", "OpenAI GPT-5 updates", "GPT-5 release date rumors"。
    *   目标：获取最新、最权威的关于 GPT-5 的新闻、官方公告和可靠分析。
2.  **使用 `web_fetch` 抓取内容**：
    *   访问搜索结果中排名前几位的相关新闻文章、官方博客和技术论坛页面。
    *   目标：获取文章的完整文本内容。
3.  **提取关键信息**：
    *   从抓取的内容中识别并提取 GPT-5 的主要进展、潜在发布日期、功能特性、性能指标、技术细节、市场影响和任何官方声明。
    *   目标：筛选出最重要和相关的信息点。
4.  **整理成简报**：
    *   将提取的关键信息汇总成一份简洁明了的简报，突出重点，并注明信息来源。
    *   目标：提供一份易于阅读、信息密集的总结。

您是否同意我按照这个计划进行？
"""

# 2. 提议并等待确认
user_confirmed = sessions_yield(plan, require_confirmation=True)

if user_confirmed:
    sessions_yield("好的，您已同意。我将开始执行计划。", type="info")
    # 3. 执行计划的实际步骤
    # search_results = web_search("GPT-5 latest news")
    # # ... (后续的 web_fetch, 信息提取, 简报生成逻辑)
    # final_brief = generate_brief(search_results)
    # sessions_yield(f"这是关于 GPT-5 的最新简报：\n{final_brief}", type="result")
else:
    sessions_yield("计划已被用户拒绝或需要修改。请提供您的反馈，以便我调整计划。", type="warning")
    # 等待用户进一步指示或重新规划
```

## 注意事项
-   **清晰和具体是关键**：提议的计划必须清晰、具体，避免模糊的措辞。用户需要准确了解你将做什么，以及为什么这样做。
-   **预估影响和资源**：在提议中简要说明潜在的影响或资源消耗（例如，"这可能需要几分钟时间并进行多次网页访问"），帮助用户做出明智的决定。
-   **准备好处理拒绝**：始终准备好处理用户拒绝的情况。这意味着你需要能够根据用户的反馈调整计划，或者在用户拒绝后优雅地退出。不要在用户拒绝后强行执行。
-   **避免过度使用**：不要对每一个微不足道的步骤都进行确认。只在任务复杂、资源密集或有潜在影响时使用此模式，以免频繁打断用户体验。
-   **迭代和细化**：如果用户要求修改，不要直接拒绝。尝试理解他们的需求，并根据反馈迭代你的计划，然后再次提议。
-   **错误处理考虑**：在提议中可以简要提及如何处理计划执行过程中可能出现的常见错误（例如，"如果某个网站无法访问，我将尝试寻找替代来源"）。