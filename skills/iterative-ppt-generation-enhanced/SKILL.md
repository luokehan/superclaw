---
name: iterative-ppt-generation-enhanced
description: 迭代式生成PPT，并具备多级渲染降级机制，确保在复杂渲染失败时仍能交付高质量内容。
version: 1.1
evolved_from: iterative-ppt-generation
evolution_type: DERIVED
---

# 增强型迭代式PPT生成

## 适用场景
在需要生成高质量、风格化PPT，且环境工具链（如 Node.js 库、Pandoc 等）可能存在不确定性时使用。该 Skill 强调“成功交付”高于“完美格式”，通过多级降级策略防止任务中断。
- 复杂的视觉需求（如深色模式、特定布局）。
- 自动化渲染脚本可能因环境依赖缺失而失败。
- 需要在生成过程中实时验证内容并确保最终产出。

## 步骤
1.  **需求分析与结构化规划**:
    *   明确主题、风格（如“深色科技感”）和页数。
    *   使用 `process` 生成详细大纲，并为每页定义 **Content Schema**（标题、要点、视觉建议）。
    *   **关键增强**：预先定义一个 `presentation_data.json` 结构，用于存储所有已确认的幻灯片数据，解耦内容与渲染。

2.  **逐页内容生成与确认**:
    *   循环执行：生成内容 -> 用户审核 -> 修正 -> 写入 JSON 缓存。
    *   使用 `write` 更新本地数据文件，确保即使进程中断，进度也能恢复。

3.  **鲁棒性渲染执行 (Multi-tiered Rendering)**:
    *   **第一级：高级渲染 (High-Fidelity)**
        尝试使用复杂的渲染引擎（如 `html2pptx` 或自定义 Node.js 脚本）。
        ```bash
        # 尝试执行高级渲染脚本
        exec "node render_fancy_ppt.js presentation_data.json --theme dark"
        ```
    *   **第二级：标准渲染 (Standard Fallback)**
        如果第一级报错（如缺少依赖），自动切换到基础工具（如 `pandoc` 或简单的 `pptxgenjs` 逻辑）。
        ```bash
        # 如果高级渲染失败，尝试 Pandoc 转换
        exec "pandoc final_content.md -o output.pptx"
        ```
    *   **第三级：结构化交付 (Safe Mode)**
        如果所有自动化转换均失败，整理一份格式完美的 Markdown 或文本文件，并提供详细的排版指南，确保用户可以快速手动完成。

4.  **验证与交付**:
    *   检查生成的 `.pptx` 文件大小和基本信息。
    *   向用户报告最终采用的生成路径（“高级渲染成功”或“已降级至标准模式”）。

## 工具和命令
- `process`: 内容创作与逻辑分析。
- `write`: 维护 `slides_cache.json`，作为渲染引擎的唯一事实来源。
- `exec`: 尝试运行不同的渲染命令。
- `read`: 读取缓存数据进行汇总。
- `canvas`: (可选) 用于生成复杂的图表图片并嵌入 PPT。

## 注意事项
-   **数据驱动**：不要直接生成格式化代码，先生成结构化数据（JSON），这样可以轻松适配不同的渲染器。
-   **静默降级**：在 `exec` 失败时，捕获错误并立即尝试下一级方案，而不是向用户报错停止。
-   **风格一致性**：在降级到文本模式时，显式说明原本设计的视觉元素（如“此处应使用深蓝色背景，白色标题”）。

## 示例
**任务**: 生成3页“量子计算的未来”深色风格PPT。

1.  **初始化数据结构**:
    ```bash
    write "ppt_data.json" "{ \"title\": \"量子计算的未来\", \"style\": \"dark\", \"slides\": [] }"
    ```

2.  **生成并确认内容 (迭代过程略)**:
    (假设已完成3页内容确认并写入 `ppt_data.json`)

3.  **执行带降级的渲染**:
    ```javascript
    // 逻辑伪代码
    try {
        // 尝试 Tier 1: 调用 html2pptx 脚本
        await exec("node html_to_pptx.js ppt_data.json");
        message("PPT 已通过高级引擎生成，应用了深色主题。");
    } catch (e) {
        try {
            // 尝试 Tier 2: 降级到 Pandoc
            await exec("pandoc temp_slides.md -o future_quantum.pptx");
            message("高级渲染引擎不可用，已使用标准模式生成 PPT。");
        } catch (e2) {
            // Tier 3: 最终保底
            read "ppt_data.json";
            message("由于环境限制无法直接生成文件，已为您整理好结构化内容与排版建议，请查收。");
        }
    }
    ```

4.  **最终交付**:
    提供 `future_quantum.pptx` 下载链接或结构化文本。