---
name: adaptive-web-search-enhanced-enhanced
description: 在参数适配基础上，强化了 Provider 级故障迁移逻辑（Failover），针对 503/429 等错误实现自动切换备选引擎，显著提升搜索任务的鲁棒性。
version: 2.0
evolved_from: adaptive-web-search-enhanced
evolution_type: DERIVED
---

# adaptive-web-search-enhanced-enhanced

## 适用场景
当需要调用 `web_search` 工具，且对搜索的可靠性、时效性及语言有特定要求时使用。该 Skill 解决了 Grok 等 Provider 不支持 `freshness` 和 `language` 参数的问题，并能在服务不可用（503/429/超时）时自动切换至 Google、Bing 或 Brave 等备选 Provider。

## 步骤
1. **识别 Provider 约束与优先级**：
   - **默认序列**：建议优先级为 Grok -> Google -> Bing -> Brave。
   - **Grok 约束**: 不支持 `freshness` 和 `language` 参数。
   - **Google / Bing / Brave / Perplexity**: 支持 `freshness` 和 `language` 参数。
2. **参数预校验与转换**：
   - 如果目标 Provider 是 **Grok**：
     - **处理 freshness**: 将其映射为自然语言（如 `pd` -> "in the last 24 hours"）并追加到 `q` 末尾，然后移除 `freshness` 参数。
     - **处理 language**: 将其映射为自然语言（如 `zh` -> "in Chinese"）并追加到 `q` 末尾，然后移除 `language` 参数。
3. **执行请求并监控状态**：调用 `web_search`。
4. **多级错误处理与故障迁移 (Failover)**：
   - **类型 A：参数错误 (unsupported_freshness / unsupported_language)**：
     - 立即按照步骤 2 的逻辑剥离不支持的参数，将需求融入 `q` 字符串后在当前 Provider 重试。
   - **类型 B：服务不可用 (503 Service Unavailable / 429 Too Many Requests / Timeout)**：
     - **触发迁移**：不要在当前 Provider 简单重试，应立即切换至序列中的下一个 Provider（如从 Grok 切换至 Google）。
     - **参数恢复**：切换后，若新 Provider 支持原生参数，必须恢复原始的 `freshness` 和 `language` 设置，并还原 `q` 为原始查询词，以获得最高精度的过滤结果。
5. **结果整合**：若所有 Provider 均尝试失败，则向用户报告具体的服务异常情况。

## 工具和命令
**针对 Grok 的参数构造示例：**
```json
{
  "q": "DeepSeek-V3 评测 in the last 24 hours in Chinese",
  "provider": "grok"
}
```

**故障迁移至 Google 的参数构造示例（恢复原生参数）：**
```json
{
  "q": "DeepSeek-V3 评测",
  "provider": "google",
  "freshness": "pd",
  "language": "zh"
}
```

## 注意事项
- **故障切换序列**：推荐路径为 `grok` -> `google` -> `bing` -> `brave`。Google 和 Bing 在稳定性上通常优于 Grok。
- **避免死循环**：在进行故障迁移时，必须记录已尝试过的 Provider 列表，禁止在单次任务中重复尝试已失败的 Provider。
- **关键词转换表**：
  - `freshness`: `pd` -> "past day", `pw` -> "past week", `pm` -> "past month"。
  - `language`: `zh` -> "in Chinese", `en` -> "in English", `jp` -> "in Japanese"。
- **静默失败处理**：如果所有 Provider 都返回 503，应告知用户“当前搜索服务压力过大，请稍后再试”，而不是持续循环。

## 示例
**场景**：用户要求搜索“最新 AI 芯片架构”，要求 24 小时内的中文结果，首选 Grok。

**执行过程**：
1. **尝试 1 (Grok)**：
   - 构造请求：`q="最新 AI 芯片架构 in the last 24 hours in Chinese"`, `provider="grok"`。
   - 结果：返回 `503 Service Unavailable`。
2. **故障迁移 (Switch to Google)**：
   - 识别到 Google 为稳定备选且支持原生过滤。
   - **还原参数**：`q="最新 AI 芯片架构"`, `provider="google"`, `freshness="pd"`, `language="zh"`。
   - 结果：成功获取高精度搜索结果。
3. **最终响应**：基于 Google 提供的数据回答用户，并在必要时说明已通过备用引擎获取信息。