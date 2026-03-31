---
name: cross-disciplinary-tech-intelligence
description: 针对 AI 与垂直行业结合的前沿方向进行深度调研，输出包含热度排行榜、市场预测及技术瓶颈分析的结构化报告。
version: 1.0
evolved_from: none
evolution_type: CAPTURED
---

# Cross-Disciplinary Tech Intelligence (交叉学科技术情报调研)

## 适用场景
当需要对 AI 与传统垂直领域（如生物医药、材料科学、能源、农业等）的交叉前沿方向进行深度扫描时使用。适用于投资尽调、科研选题、产品战略分析。

## 步骤
1. **多维关键词构建**：
   - 组合“AI 技术项”（如 LLM, Diffusion, GNN）与“领域业务项”（如 Protein Folding, Drug Discovery, Carbon Capture）。
   - 包含中英文双语关键词，确保覆盖全球学术与商业动态。

2. **多源数据检索**：
   - **学术维度**：检索 Arxiv, Google Scholar, PubMed 过去 12-24 个月的核心论文。
   - **资本维度**：检索 Crunchbase, IT 桔子或新闻报道，识别近期的融资事件、金额及领投方。
   - **商业维度**：检索头部企业（如 Google DeepMind, NVIDIA BioNeMo）的最新产品发布或合作伙伴关系。

3. **热度矩阵分析 (Heat Ranking)**：
   - 对识别出的细分方向进行评分（1-10分）：
     - 融资热度（资金流入量）
     - 学术热度（论文引用与发布频率）
     - 商业化进度（是否有落地产品或临床/实验阶段）

4. **技术瓶颈与摩擦力识别**：
   - 分析 AI 模型在特定领域的局限性（如数据稀缺、实验验证周期长、跨学科人才断层）。

5. **结构化报告输出**：
   - 汇总上述信息，形成包含市场规模预测（引用权威机构数据）和技术路线图的报告。

## 工具和命令
- **web_search**: 
  - `web_search(query="AI for drug discovery funding 2023..2024")`
  - `web_search(query="site:arxiv.org 'Large Language Models' AND 'Genomics'")`
- **memory_search**: 用于检索历史调研记录，避免重复工作并对比趋势变化。
- **exec**: 使用 Python 进行简单的数据清洗或生成热力图（如有结构化数据）。

## 注意事项
- **避免通用化**：不要只谈 AI 的强大，必须深入到具体的领域问题（如：不是“AI 改变生物”，而是“扩散模型如何解决蛋白质侧链预测的效率问题”）。
- **数据时效性**：交叉学科变化极快，必须强制搜索过去一年内的数据。
- **交叉验证**：商业宣传往往夸大其词，需通过学术论文的实验数据进行交叉比对。

## 示例
**任务**：调研 AI + 碳捕集 (Carbon Capture) 的现状。

**执行片段**：
1. `web_search("AI driven carbon capture materials discovery 2024")`
2. `web_search("Carbon capture AI startups funding list")`
3. 识别出核心瓶颈：高通量实验验证速度远低于 AI 筛选速度。
4. 输出报告：
   - **热度排行**：MOF 材料筛选 (高), 吸收塔过程优化 (中)。
   - **市场预测**：预计 2030 年相关 AI 驱动的碳减排市场将达 X 亿美元。
   - **技术瓶颈**：缺乏标准化的材料性能数据集。