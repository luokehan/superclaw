---
name: gemini-video-understanding-enhanced
description: 基于 Gemini 3.1 Pro 的多模态理解增强版，支持多视频对比综述、差异化提取与综合教程生成。
version: 1.1
evolved_from: gemini-video-understanding
evolution_type: DERIVED
---

# Gemini 多模态理解增强版 (支持多视频对比)

模型：**gemini-3.1-pro-preview**（利用其 2M 上下文处理多视频关联分析）

本工具集在基础多模态理解之上，增强了**多源信息融合**能力。适用于需要对比多个视频教程、汇总多条小红书笔记或从多张图片中提取演变规律的场景。

## 适用场景
- **多视频对比**：对比不同博主的同类教程，提取最优路径，识别各家独有技巧。
- **长视频综述**：对系列视频进行跨集总结，生成知识图谱。
- **多模态溯源**：结合图片、视频和小红书笔记，还原事件全貌或产品细节。

## 步骤
1. **环境准备**：确保 `source /root/openclaw-fusion/data/.env` 已加载。
2. **输入聚合**：收集所有关联素材（视频、图片或 URL）。
3. **编写综合指令**：在 prompt 中明确要求“对比”、“找差异”或“生成矩阵”。
4. **执行分析**：使用增强命令调用脚本。
5. **结果校验**：检查生成的 Markdown 是否包含对比表格或差异化说明。

## 工具和命令

### 1. 增强型视频对比与综述 (video-understand.py)
利用 Gemini 3.1 Pro 的超长上下文，同时输入多个视频进行分析。

```bash
source /root/openclaw-fusion/data/.env

# 多视频对比：分析两个视频在同一操作上的差异
python3 /root/openclaw-fusion/skills/gemini-video-understanding/video-understand.py \
  "对比这两个视频的教学方法。请用表格列出：1. 共同步骤 2. 视频A独有技巧 3. 视频B独有技巧 4. 最终推荐的最优方案" \
  --input video_vlog_1.mp4 video_vlog_2.mp4 --output comparison_report.md

# 跨平台综述：YouTube 视频与本地视频结合分析
python3 /root/openclaw-fusion/skills/gemini-video-understanding/video-understand.py \
  "结合这两个视频，总结该产品的优缺点" \
  --input https://www.youtube.com/watch?v=example1 local_review.mp4 --low-res
```

### 2. 批量图片演变分析 (image-understand.py)
```bash
# 分析一组截图，描述软件 UI 的演变过程或操作流程的逻辑顺序
python3 /root/openclaw-fusion/skills/gemini-video-understanding/image-understand.py \
  "按照时间顺序排列这些截图，并说明每一步的功能变化" \
  --input step1.png step2.png step3.png --output workflow.md
```

### 3. 小红书多笔记聚合 (xhs-note-reader.py)
```bash
# 针对特定话题，连续分析多条笔记并汇总（需手动多次执行或配合脚本循环）
# 建议先将笔记内容保存为 md，再统一交给 Gemini 综述
python3 /root/openclaw-fusion/skills/gemini-video-understanding/xhs-note-reader.py \
  <url_1> --output note1.md
python3 /root/openclaw-fusion/skills/gemini-video-understanding/xhs-note-reader.py \
  <url_2> --output note2.md
```

## 注意事项
- **Token 墙**：多视频分析会极速消耗 Token。处理 2 个以上 5 分钟视频时，**务必使用 `--fps 0.5` 或 `--low-res`**。
- **Prompt 技巧**：在多视频对比时，必须在 Prompt 中指明“视频A”、“视频B”（按输入顺序对应），否则模型可能混淆来源。
- **并发限制**：Gemini API 对多模态大文件上传有并发限制，若报错 `429`，请分批处理或增加延时。
- **视频长度**：单个任务建议总视频时长不超过 30 分钟，以保证分析精度。

## 示例：生成对比矩阵
**任务**：对比两款扫地机器人的测评视频。
**命令**：
```bash
python3 /root/openclaw-fusion/skills/gemini-video-understanding/video-understand.py \
  "请对比这两个测评视频。视频1是品牌X，视频2是品牌Y。请重点关注：1. 避障能力 2. 噪音分贝 3. 自动集尘效率。请以 Markdown 表格形式输出对比矩阵。" \
  --input brand_x_review.mp4 brand_y_review.mp4 --fps 1 --output robot_comparison.md
```
**预期输出**：
包含“功能指标 | 品牌X表现 | 品牌Y表现 | 胜出者”的详细表格及文字总结。