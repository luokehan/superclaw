---
name: labclaw-bio-bioinformatics-enhanced
description: 增强型生物信息学分析技能，特别优化了 Bioconductor 文档获取的鲁棒性与多源检索逻辑。
version: 1.0
evolved_from: bioinformatics-analysis
evolution_type: DERIVED
---

# LabClaw Bioinformatics Enhanced

## 适用场景
适用于转录组（RNA-seq）、单细胞转录组（scRNA-seq）、全基因组关联分析（GWAS）等生物信息学分析任务。特别强化了在网络环境不稳定或官方链接失效时，获取 Bioconductor 及其它生物信息学工具文档的能力。

## 核心工作流

### 1. 文档获取与环境检查 (增强版)
在开始任何分析前，必须确认工具版本与文档的匹配度。
- **Bioconductor 文档检索策略**：
    1. **首选官方 Release**: `https://bioconductor.org/packages/release/bioc/html/[Package].html`
    2. **备选 GitHub 镜像**: 若官方重定向失败，访问 `https://github.com/Bioconductor/[Package]` 查看 README 或 `/vignettes` 目录。
    3. **归档检索**: 若当前版本不匹配，访问 `https://bioconductor.org/packages/3.x/bioc/html/[Package].html` (替换 3.x 为对应版本)。
    4. **搜索引擎降级**: 使用 `web_search` 搜索 `site:bioconductor.org [Package] vignette filetype:pdf`。

### 2. RNA-seq 分析
1. **质控**: FastQC, MultiQC。
2. **比对/定量**: STAR/featureCounts 或 Salmon/Kallisto (准比对)。
3. **差异表达**: 
   - 使用 `DESeq2` (推荐) 或 `edgeR`。
   - 必须执行 `vst` 或 `rlog` 转换进行可视化。
4. **功能富集**: `clusterProfiler` (GO/KEGG), `fgsea` (GSEA)。

### 3. scRNA-seq 分析 (Scanpy/Seurat)
1. **预处理**: 过滤线粒体高表达细胞（通常 >5%-20%）、低基因计数细胞。
2. **标准化**: `LogNormalize` (Seurat) 或 `log1p` (Scanpy)。
3. **降维与聚类**: PCA -> UMAP/tSNE -> Leiden/Louvain 聚类。
4. **注释**: 依据 Marker genes 手动注释或使用 `SingleR` 等工具。

### 4. GWAS / 基因组学
1. **质控**: PLINK 处理 MAF, HWE, Call rate。
2. **关联测试**: PLINK 或 REGENIE (处理群体结构)。
3. **可视化**: 绘制 Manhattan 图和 Q-Q 图。

## 工具和命令

### R / Bioconductor 环境管理
```R
# 鲁棒的安装脚本
if (!require("BiocManager", quietly = TRUE))
    install.packages("BiocManager")

# 检查特定包的文档位置
browseVignettes("DESeq2") 
```

### 常用文件处理
- **SAM/BAM 处理**: `samtools view -bS sample.sam > sample.bam`
- **VCF 过滤**: `bcftools filter -i 'QUAL>30 && DP>10' input.vcf -o filtered.vcf`
- **AnnData 转换 (Python)**: `adata.write_h5ad("output.h5ad")`

## 注意事项
- **版本陷阱**: Bioconductor 版本与 R 版本严格绑定。在检索文档时，务必确认当前 R 版本（`R.version.string`）。
- **重定向问题**: Bioconductor 官网常有 JS 重定向，`web_fetch` 失败时应立即切换到 GitHub 镜像源。
- **内存管理**: 处理单细胞数据或大基因组 BAM 文件时，优先使用流式处理或增加 Swap。
- **物种基因名**: 始终明确基因 ID 类型（Ensembl ID, Symbol, Entrez ID），转换时使用 `org.Hs.eg.db` 等标准数据库。

## 示例：获取失效的 Bioconductor 文档
若 `https://bioconductor.org/packages/release/bioc/html/DESeq2.html` 无法直接访问：
1. 调用 `web_search(query="DESeq2 Bioconductor GitHub mirror")`。
2. 访问 `https://github.com/mikelove/DESeq2` 或 `https://github.com/Bioconductor/DESeq2`。
3. 在 `vignettes/` 目录下寻找 `.Rmd` 或 `.pdf` 文件。
4. 解析 Rmd 中的示例代码作为分析参考。