---
name: download_scientific_paper-enhanced
description: 从给定URL下载科学论文，包含针对反爬和Cookie限制的自动重试逻辑。
version: 1.0
evolved_from: download_scientific_paper
evolution_type: DERIVED
---

# 下载科学论文 (增强版)

## 适用场景
当你拥有一个科学论文（如PDF、HTML）的直接下载链接，需要将其下载到本地时。此增强版特别适用于常规 `web_fetch` 失败、遇到 `cookies_not_supported` 错误或被网站反爬机制拦截的场景。

## 步骤
1.  **获取论文URL**: 确认要下载的科学论文的直接下载链接。
2.  **尝试常规下载**: 首先使用 `web_fetch` 尝试下载。
3.  **检测失败状态**: 检查 `web_fetch` 的返回结果。如果出现以下情况，则判定为失败：
    - 报错信息包含 `cookies_not_supported`。
    - 下载的文件大小极小（例如 < 1KB）。
    - 使用 `file` 命令发现下载的是 HTML 页面而非 PDF。
4.  **执行底层回退 (Fallback)**: 如果常规下载失败，使用 `exec` 调用 `curl` 命令。通过模拟浏览器 User-Agent 和跟随重定向（-L）来绕过限制。
5.  **验证文件类型**: 使用 `exec file` 验证最终下载的文件是否为预期的格式（如 PDF）。
6.  **重命名与整理**: 将文件重命名为具有描述性的名称。

## 工具和命令

*   **`web_fetch`**: 基础下载工具。
    *   `web_fetch --url <URL> --output <FILE>`
*   **`exec curl` (关键回退工具)**: 用于模拟底层请求。
    *   `exec curl -L -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" -o <本地文件名> <URL>`
    *   `-L`: 跟随重定向（对学术站点非常重要）。
    *   `-A`: 设置 User-Agent，防止因“非浏览器访问”被拦截。
*   **`exec file`**: 验证文件真实格式。
    *   `exec file <本地文件名>`
*   **`exec mv`**: 重命名文件。

## 注意事项
-   **Cookie 限制**: 某些数据库（如 IEEE, ScienceDirect）强制要求 Cookie。如果 `curl` 依然失败，可能需要从 `sessions_yield` 中提取有效会话信息。
-   **User-Agent 伪装**: 始终使用现代浏览器的 User-Agent，避免使用 `curl/7.x.x` 默认标识，否则极易触发 403 Forbidden。
-   **静默失败**: 即使 `curl` 返回状态码 0，也可能下载了一个“访问受限”的 HTML 页面。**必须**通过 `file` 命令检查内容。
-   **重定向陷阱**: 很多论文链接会经过多次重定向，`curl` 必须带上 `-L` 参数。

## 示例

假设下载 GPT-5 相关研究论文，URL 为 `https://arxiv.org/pdf/2403.xxxxx.pdf`。

```bash
# 1. 尝试常规下载
web_fetch --url https://arxiv.org/pdf/2403.xxxxx.pdf --output paper_v1.pdf

# 2. 检查发现 paper_v1.pdf 是 HTML 或下载失败 (假设触发了反爬)
# 3. 使用增强回退方案
exec curl -L -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36" -o gpt5_research.pdf https://arxiv.org/pdf/2403.xxxxx.pdf

# 4. 验证类型
exec file gpt5_research.pdf
# 输出应包含: PDF document, version 1.x

# 5. 整理
exec mv gpt5_research.pdf "Latest_GPT-5_Technical_Report.pdf"
```