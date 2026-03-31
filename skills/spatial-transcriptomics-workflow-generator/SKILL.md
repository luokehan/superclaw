---
name: spatial-transcriptomics-workflow-generator
description: 根据特定空间转录组技术（如 Visium, Xenium）自动生成基于 Python (Squidpy) 或 R (Seurat/Giotto) 的标准分析流水线。
version: 1.0
evolution_type: CAPTURED
---

# Spatial Transcriptomics Workflow Generator

## 适用场景
当用户提供空间转录组数据（如 10x Visium, Xenium, MERFISH, Slide-seq）并要求进行下游分析（质控、聚类、空间统计、细胞交互）时使用。

## 步骤
1. **技术识别**：识别数据来源（测序型如 Visium，或成像型如 Xenium/CosMx）以决定预处理策略。
2. **框架选择**：根据用户偏好选择 Python (Scanpy + Squidpy) 或 R (Seurat + Giotto) 路径。
3. **数据加载**：编写针对特定格式（H5, MTX, Parquet, GeoJSON）的加载代码。
4. **预处理与质控**：
    - 过滤低质量点/细胞。
    - 标准化（SCTransform 或 LogNormalize）。
    - 降维（PCA, UMAP/t-SNE）。
5. **空间特征提取**：
    - 构建空间邻接图（Spatial Neighbors）。
    - 计算空间变量基因（Spatial Variable Genes, 如 Moran's I）。
6. **高级分析**：
    - 空间聚类（SNN, Leiden）。
    - 邻域富集分析（Neighborhood Enrichment）。
    - 细胞类型解卷积（针对低分辨率技术如 Visium）。
7. **可视化**：生成空间表达图、聚类图及交互分析图。

## 工具和命令
### Python (Squidpy/Scanpy)
```python
import scanpy as sc
import squidpy as sq

# 加载 Visium
adata = sq.read.visium("path/to/data")
# 构建空间图
sq.gr.spatial_neighbors(adata)
# 空间富集分析
sq.gr.nhood_enrichment(adata, cluster_key="clusters")
# 可视化
sq.pl.spatial_scatter(adata, color="clusters", shape=None)
```

### R (Seurat)
```R
library(Seurat)
library(ggplot2)

# 加载 Visium
data <- Load10X_Spatial(data.dir = "path/to/data")
# 标准化
data <- SCTransform(data, assay = "Spatial", verbose = FALSE)
# 空间差异基因
de_markers <- FindSpatiallyVariableFeatures(data, assay = "SCT", selection.method = "markvariogram")
# 可视化
SpatialPlot(data, features = "gene-name")
```

## 注意事项
- **内存管理**：成像型技术（Xenium/CosMx）数据量极大，建议在 Python 中使用 `dask` 或在 R 中进行子采样。
- **坐标对齐**：在处理多切片数据时，务必检查坐标系是否统一，避免空间邻域计算错误。
- **分辨率差异**：Visium 是多细胞点（Spot），而 Xenium 是单细胞分辨率，分析逻辑需相应调整（如 Visium 需做解卷积）。
- **环境依赖**：Squidpy 依赖 `omnipath` 进行配体-受体分析，需确保网络连接或本地数据库可用。

## 示例
**任务**：为 10x Visium 数据生成 Python 分析脚本。
**输出片段**：
```python
# 1. Load Data
adata = sq.read.visium("./outs/", library_id="sample1")
adata.var_names_make_unique()

# 2. QC & Preprocessing
sc.pp.calculate_qc_metrics(adata, inplace=True)
sc.pp.filter_cells(adata, min_counts=500)
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)

# 3. Spatial Analysis
sq.gr.spatial_neighbors(adata)
sq.gr.spatial_autocorr(adata, mode="moran") # 计算空间自相关

# 4. Plotting
sq.pl.spatial_scatter(adata, color="total_counts", img_res="lowres")
```