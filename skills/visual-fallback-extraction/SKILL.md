---
name: visual-fallback-extraction
description: 当结构化抓取失败时，通过浏览器截图与多模态视觉分析还原页面内容。
version: 1.0
evolution_type: CAPTURED
---

# Visual Fallback Extraction (视觉后备提取)

## 适用场景
- **反爬拦截**：目标网站启用了复杂的反爬虫机制（如 Cloudflare 等待、人机验证），导致常规 DOM 抓取工具失效。
- **结构剧变**：页面 CSS 选择器或 DOM 结构频繁变动，导致预设的抓取脚本崩溃。
- **动态渲染**：内容高度依赖 JavaScript 异步加载，且常规等待逻辑难以捕获完整数据。
- **多媒体平台**：社交媒体（Twitter/X, Instagram, 小红书）的动态流内容。

## 步骤
1. **环境准备**：调用 `browser` 工具访问目标 URL。
2. **页面渲染**：执行 `browser_press_key` (如 PageDown) 或 `browser_scroll` 确保懒加载内容已触发。
3. **视觉捕获**：
   - 使用 `browser_screenshot` 截取当前视口。
   - 如果内容较长，执行分段截图。
4. **多模态分析**：将截图发送至支持视觉识别的模型（如 Gemini 1.5 Pro）。
5. **结构化输出**：在 Prompt 中定义严格的输出格式（如 JSON），要求模型根据图片内容还原文本。
6. **后处理**：校验模型输出的数据是否符合业务逻辑。

## 工具和命令
- **截图工具**：`browser_screenshot`
- **视觉模型**：`gemini-1.5-pro` 或 `gemini-1.5-flash`
- **Prompt 模板**：
  ```text
  你是一个高精度的网页数据提取专家。请分析提供的截图，并提取以下信息：
  1. [字段A]: 描述
  2. [字段B]: 描述
  请以 JSON 格式输出，确保数值准确，不要包含任何推测内容。如果图片中不存在该信息，请填入 null。
  ```

## 注意事项
- **分辨率**：确保截图清晰度足以辨认最小字号的文本。
- **遮挡物**：注意关闭或避开页面弹窗、Cookie 确认框，以免遮挡关键数据。
- **Token 消耗**：视觉分析比纯文本分析消耗更多 Token，建议仅在 `fetch` 或 `selector` 失败后作为 Fallback 触发。
- **隐私**：截图可能包含敏感信息（如登录状态、个人头像），在处理公共数据提取时需注意合规性。

## 示例
**任务**：提取一条因反爬无法抓取的 Twitter 推文内容。
1. `browser_navigate(url="https://twitter.com/user/status/123")`
2. `browser_wait(selector="article", timeout=5000)`
3. `browser_screenshot()` -> 得到 `screenshot.png`
4. **模型输入**：
   "提取这张推文截图中的：作者用户名、推文正文、发布时间、转发数、点赞数。"
5. **模型输出**：
   ```json
   {
     "author": "@OpenAI",
     "content": "Introducing Sora, our text-to-video model...",
     "timestamp": "2024-02-15",
     "retweets": "150K",
     "likes": "500K"
   }
   ```