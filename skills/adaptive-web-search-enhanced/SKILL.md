---
name: adaptive-web-search-enhanced
description: 增加调用前的 Provider 参数兼容性预检，防止 Grok 因不支持 freshness 等参数导致的冗余报错与重试。
version: 1.4
evolved_from: adaptive-web-search-enhanced
evolution_type: FIX
---

# adaptive-web-search-enhanced

## 适用场景
当需要调用 `web_search` 工具，且对搜索的时效性（freshness）或语言（language）有特定要求时使用。该 Skill 重点解决了 Grok 引擎不支持原生过滤参数的问题，通过预检机制避免 `unsupported_freshness` 错误。

## 步骤
1. **参数预检 (Pre-flight Check)**：
   - 在构造 `web_search` 调用前，检查 `provider` 字段。
   - 如果 `provider` 为 `grok`：
     - 检查是否存在 `freshness` 或 `language` 参数。
     - 若存在，必须执行**步骤 2** 的修正逻辑，严禁直接带参数调用。
2. **自动修正与适配**：
   - **方案 A（优先 - 切换 Provider）**：若业务对时效性精度要求高，将 `provider` 修改为 `brave` 或 `perplexity`。
   - **方案 B（降级 - 参数注入）**：若必须使用 `grok`，则：
     - 将 `freshness` 映射为自然语言（如 `pd` -> "in the last 24 hours"）追加到 `q` 末尾。
     - 将 `language` 映射为自然语言（如 `zh` -> "in Chinese"）追加到 `q` 末尾。
     - **必须从参数列表中彻底移除 `freshness` 和 `language` 字段**。
3. **执行请求**：调用 `web_search`。
4. **故障迁移 (Failover)**：
   - 若请求返回 `503`、`429` 或超时，按照 `Grok -> Brave -> Perplexity` 序列切换。
   - 切换到支持原生的 Provider 时，应恢复 `freshness` 和 `language` 参数以获得最佳效果。

## 工具和命令
**预检修正示例 (针对 Grok)：**

```json
// 错误做法：直接调用会导致 unsupported_freshness
// 正确做法（方案 B）：
{
  "q": "DeepSeek-V3 评测 in the last 24 hours",
  "provider": "grok" 
  // 注意：此处已移除 freshness 参数
}
```

**预检修正示例 (方案 A)：**

```json
{
  "q": "DeepSeek-V3 评测",
  "provider": "brave",
  "freshness": "pd"
}
```

## 注意事项
- **硬性拦截**：Grok 明确不支持 `freshness`。一旦在请求中包含该参数，API 将返回 `unsupported_freshness` 错误。
- **参数映射表**：
  - `pd` (past day) -> "in the last 24 hours"
  - `pw` (past week) -> "in the past week"
  - `pm` (past month) -> "in the past month"
- **性能优化**：通过预检减少一次无效的 API 往返，提升响应速度。

## 示例
**场景**：用户要求“搜索最近一天的比特币价格”，指定使用 Grok。

**执行过程**：
1. **预检**：发现 `provider="grok"` 且有 `freshness="pd"` 需求。
2. **决策**：为了满足用户对 Grok 的偏好，采用参数注入逻辑。
3. **构造调用**：
   ```json
   {
     "q": "bitcoin price in the last 24 hours",
     "provider": "grok"
   }
   ```
4. **结果**：成功获取结果，未触发 `unsupported_freshness` 报错。