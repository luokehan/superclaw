---
name: cli-anything-guide
description: CLI-Anything 使用指南 — Agent 通过 CLI 操控桌面软件
---

# CLI-Anything 工具指南

CLI-Anything 将桌面软件 CLI 化，让 Agent 能通过命令行操控图形应用。

## 安装目标软件的 CLI

```bash
# 先安装桌面软件（按需）
apt-get install -y blender gimp inkscape libreoffice

# 再安装对应的 CLI harness
cd /root/CLI-Anything/<software>/agent-harness
pip install -e .
```

## 任务中的典型用法

### 图像处理任务
```bash
cli-anything-gimp --json resize --input input.png --width 1200 --height 800 --output resized.png
cli-anything-gimp --json apply-filter --input photo.jpg --filter sharpen --output sharp.jpg
```

### 文档转换任务
```bash
cli-anything-libreoffice --json convert --input report.docx --format pdf --output report.pdf
cli-anything-libreoffice --json export --input data.xlsx --format csv --output data.csv
```

### 3D 渲染任务
```bash
cli-anything-blender --json render --scene model.blend --output render.png
```

### 矢量图处理
```bash
cli-anything-inkscape --json export --input logo.svg --format png --dpi 300 --output logo.png
```

### 浏览器自动化
```bash
cli-anything-browser navigate "https://example.com"
cli-anything-browser screenshot --output page.png
cli-anything-browser extract --selector ".article-content"
```

## 注意事项

- 所有命令加 `--json` 获取结构化输出
- 目标软件必须已安装在系统上
- 首次使用某软件的 CLI 需先 `pip install -e .`
