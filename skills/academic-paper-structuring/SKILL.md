---
name: academic-paper-structuring
description: 提供标准学术论文的结构化框架及各章节（如摘要字数要求、方法论细节、结论逻辑等）的写作规范指导。
version: 1.0
evolution_type: CAPTURED
---

# Academic Paper Structuring (学术论文结构化指南)

## 适用场景
- 撰写学术论文初稿或大纲。
- 对现有论文结构进行标准化审查。
- 准备期刊投稿或会议论文。

## 步骤
1. **构建核心大纲**：按照 IMRaD (Introduction, Methods, Results, and Discussion) 逻辑建立一级标题。
2. **填充章节细节**：
    - **Title**: 确保简洁（10-15词），包含核心变量和研究对象。
    - **Abstract**: 遵循“背景-目的-方法-结果-结论”五部曲，字数控制在 150-250 字。
    - **Introduction**: 采用“漏斗式”写法，从宏观背景引向具体的研究缺口（Research Gap）。
    - **Methods**: 详细描述实验设计、数据来源、工具及分析方法，以确保可重复性。
    - **Results**: 仅陈述事实和数据，使用图表辅助，不进行主观推论。
    - **Discussion**: 解释结果意义，与前人研究对比，承认研究局限性。
    - **Conclusion**: 总结主要发现，提出政策建议或未来研究方向。
    - **References**: 检查引用格式一致性（如 APA, IEEE, MLA）。
3. **逻辑一致性检查**：确保摘要中的结论与正文结果一致，引言中的科学问题在讨论中得到回答。

## 工具和命令
- **Markdown/LaTeX**: 用于结构化排版。
- **Pandoc**: `pandoc input.md -o output.pdf --citeproc` (用于转换格式并处理引用)。
- **Checklist 命令**: 
  - `grep -i "significant" results.md` (检查结果显著性描述)。
  - `wc -w abstract.md` (检查摘要字数)。

## 注意事项
- **避免混淆 Results 与 Discussion**：Results 告诉读者“发现了什么”，Discussion 告诉读者“这意味着什么”。
- **时态规范**：已完成的方法和结果通常用过去时；普遍真理和当前结论用一般现在时。
- **自洽性**：确保文中提到的所有缩写在第一次出现时均有定义。
- **引用完整性**：文中引用的每一处文献必须出现在参考文献列表中，反之亦然。

## 示例
### Abstract 结构示例：
[Background] With the rise of AI, data privacy has become critical. [Objective] This study aims to evaluate the efficiency of federated learning in medical imaging. [Methods] We conducted a comparative analysis of three algorithms using the MNIST dataset. [Results] Our findings show a 15% increase in accuracy while maintaining 99% privacy. [Conclusion] Federated learning is a viable solution for secure medical data processing.

### Introduction 逻辑链：
1. 全球变暖的现状 (Broad Context)
2. 现有碳捕集技术的局限 (Research Gap)
3. 本文提出的新型催化剂 (Your Contribution)
4. 本文的结构安排 (Paper Roadmap)