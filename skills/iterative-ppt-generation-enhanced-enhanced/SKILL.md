---
name: iterative-ppt-generation-enhanced-enhanced
description: 针对长耗时、高复杂度（多形状）PPT 任务的断点续传与分段提交增强版，专门应对 SIGTERM 及执行超时。
version: 1.2
evolved_from: iterative-ppt-generation-enhanced
evolution_type: DERIVED
---

# 弹性复杂 PPT 生成 (增强版)

## 适用场景
当 PPT 包含大量元素（如单页超过 40 个形状）、逻辑复杂或执行环境存在严格的时间限制（如 10 分钟超时导致 SIGTERM）时。该 Skill 强调“原子化操作”和“状态实时持久化”。

## 步骤
1.  **初始化状态追踪器**:
    *   创建一个 `state.json` 文件，记录总页数、当前处理页码、已完成的形状索引及转换状态。
    ```bash
    echo '{"current_slide": 0, "completed_shapes": 0, "status": "init"}' > state.json
    ```

2.  **分段式处理循环**:
    *   **不要**在一个 `exec` 命令中处理整个 PPT。
    *   将任务拆分为“单页处理”单元。每处理完一页，立即更新 `state.json` 并执行一次 `write` 操作保存中间产物。
    *   对于极其复杂的页面（如包含 50+ shapes），进一步拆分为“形状组”处理。

3.  **断点自动恢复逻辑**:
    *   在每次 `exec` 开始前，读取 `state.json`。
    *   如果检测到 `status: "processing"` 且 `current_slide > 0`，则自动加载对应的 `slide_n.pptx` 或中间状态。

4.  **应对 SIGTERM 信号**:
    *   在 Python 脚本中注册信号处理函数，捕获 `SIGTERM`。
    *   被终止前，强制执行 `prs.save('temp_checkpoint.pptx')` 并更新 `state.json`。

5.  **增量合并与校验**:
    *   所有页面处理完成后，使用专门的合并脚本将各页 `pptx` 组合。
    *   执行最终校验：不仅校验幻灯片数量，还要校验关键形状（Shapes）的计数。

    ```bash
    # 校验特定页面的形状数量（通过解析 XML）
    unzip -p final.pptx ppt/slides/slide9.xml | grep -o '<p:sp>' | wc -l
    ```

## 工具和命令
-   **状态管理**: `jq` 用于在命令行快速读写 `state.json`。
    -   读取：`current=$(jq -r '.current_slide' state.json)`
    -   更新：`jq '.current_slide += 1' state.json > tmp.json && mv tmp.json state.json`
-   **原子保存**: 在 Python 中使用 `python-pptx` 时，每完成一个 `shape` 的关键属性修改即进行一次 `try-except` 包裹。
-   **信号捕获 (Python)**:
    ```python
    import signal, sys
    def signal_handler(sig, frame):
        prs.save('interrupted_state.pptx')
        sys.exit(0)
    signal.signal(signal.SIGTERM, signal_handler)
    ```

## 注意事项
-   **内存管理**: 处理超大 PPT 时，频繁保存会增加 IO 开销，但在不稳定的执行环境中，IO 开销优于任务全盘失败。
-   **路径一致性**: 确保断点恢复时使用的文件路径与中断前完全一致。
-   **Ghosting 预防**: 在处理复杂形状位移（Ghosting）时，记录每个 shape 的原始 ID，避免因中断导致 ID 偏移。

## 示例
**场景**: 处理一个 13 页的 PPT，在第 9 页处理到第 25 个形状时遭遇 SIGTERM。

1.  **检测中断**:
    ```bash
    cat state.json
    # 输出: {"current_slide": 9, "last_shape": 25, "status": "interrupted"}
    ```

2.  **恢复执行**:
    *   脚本读取 `state.json`，直接定位到 Slide 9。
    *   加载 `slide_9_partial.pptx`。
    *   从 Shape 26 开始继续执行 `Ghosting` 或 `Update` 操作。

3.  **分段提交**:
    *   完成 Slide 9 后，立即执行：
    ```bash
    # 更新状态并保存
    jq '.status = "slide_9_complete"' state.json > state.json.tmp && mv state.json.tmp state.json
    ```
    *   即使后续 Slide 10 失败，Slide 9 的成果已固化。