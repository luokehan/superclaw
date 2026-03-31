---
name: ppt-ghosting-transition-logic
description: 通过在后续幻灯片中保留并淡化前一页形状（Ghosting）来增强 PPT 视觉连贯性的逻辑。
version: 1.0
evolution_type: CAPTURED
---

# ppt-ghosting-transition-logic

## 适用场景
在自动化生成多页 PPT 时，当一个主题或流程跨越多个幻灯片，需要通过视觉引导让观众感知到内容的变化和延续。特别适用于：
- 复杂的流程图分步拆解。
- 形状在幻灯片之间发生位移或缩放的动画模拟。
- 保持上下文关联，防止观众在翻页时失去焦点。

## 步骤
1. **识别锚点形状 (Anchor Shapes)**：从当前幻灯片（Slide N）中提取需要延续到下一页（Slide N+1）的关键形状。
2. **执行克隆 (Cloning)**：将识别出的形状及其属性（尺寸、文本、原始坐标）复制到目标幻灯片。
3. **应用 Ghosting 样式**：
    - **透明度调整**：将克隆形状的填充和轮廓透明度设置为 50%-80%。
    - **去色处理**：如果支持，将形状颜色转换为灰色调或淡色调。
    - **层级置底**：将 Ghost 形状移动到目标幻灯片的底层（Z-order bottom），避免干扰新内容。
4. **坐标偏移计算 (Offset Calculation)**：
    - 根据目标幻灯片的布局，计算 Ghost 形状的新坐标。
    - 如果是平移过渡，应用 `delta_x` 和 `delta_y`。
5. **过渡验证 (Transition Verification)**：检查 Slide N 的结束状态与 Slide N+1 的起始 Ghost 状态是否在视觉上对齐。

## 工具和命令
假设使用 Python 处理 PPT 自动化：
```python
# 示例：设置形状透明度 (需要处理 XML，因为 python-pptx 原生支持有限)
from pptx.oxml.xmlchemy import OxmlElement

def set_shape_transparency(shape, alpha):
    """alpha: 0-100, 100 为完全透明"""
    adst = OxmlElement('a:alphaMod')
    adst.set('val', str((100 - alpha) * 1000))
    shape.fill._fill.get_or_add_solidFill().get_or_add_srgbClr().append(adst)

# 示例：计算并更新坐标
new_x = prev_shape.left + offset_cm * 360000  # 1cm = 360000 EMU
new_y = prev_shape.top + offset_cm * 360000
```

## 注意事项
- **性能开销**：过多的 Ghost 形状会增加 PPT 文件体积和渲染压力，建议每页 Ghost 形状不超过 5 个。
- **Z-Order 冲突**：务必确保 Ghost 形状位于最底层，否则会遮挡目标页面的交互式内容或文字。
- **文本处理**：Ghost 形状内的文本通常也需要淡化或直接移除，以减少视觉噪音。
- **坐标系一致性**：在计算偏移时，注意 PPT 的坐标原点（左上角）以及不同模板可能的边距差异。

## 示例
**场景**：Slide 9 展示了三个核心模块，Slide 10 开始详细讲解模块 A。
- **操作**：
    1. 在 Slide 10 中，将 Slide 9 的三个模块形状全部克隆。
    2. 将模块 B 和 C 的透明度设为 70%，并移动到幻灯片左侧边缘作为背景。
    3. 模块 A 保持高亮或作为过渡动画的起点。
- **日志表现**：
    `[Ghosting 3 content shape(s) on slide 10...]`
    `Updated /slide[10]/shape[25]: x=2cm, alpha=70%`
    `✓ Transition verified on slide 10`