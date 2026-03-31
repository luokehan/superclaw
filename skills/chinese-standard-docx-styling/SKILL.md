---
name: chinese-standard-docx-styling
description: 专门用于生成符合中国标准公文或专业报告格式的 DOCX 技能，修复了文件路径权限及沙盒环境下的保存逻辑。
version: 1.1
evolved_from: chinese-standard-docx-styling
evolution_type: FIX
---

# Skill 名称：chinese-standard-docx-styling

## 适用场景
当需要在受限环境（如自动化脚本、沙盒环境）中生成符合中国标准公文（如党政机关公文格式 GB/T 9704-2012）、专业报告或学术论文格式的 Word 文档（.docx）时使用。

## 步骤
1. **环境准备**：安装 `python-docx`。
2. **路径安全检查**：在保存前，确保目标目录存在，并**优先使用当前工作目录的相对路径**，避免使用 `/root/` 等受限绝对路径。
3. **初始化文档与页面设置**：设置 A4 纸张及标准页边距（上 3.7cm, 下 3.5cm, 左 2.8cm, 右 2.6cm）。
4. **全局样式定义**：定义正文及标题的默认字体。
5. **中文字体双重设置**：利用 `qn` 模块同时设置 `w:eastAsia` 属性，确保中文字体生效。
6. **段落格式化**：设置首行缩进（2 字符）、行间距（固定值 28-30 磅）及两端对齐。
7. **安全保存**：使用相对路径保存文件，并返回可访问的路径供后续工具（如 `message`）调用。

## 工具和命令
### 核心依赖
```bash
pip install python-docx
```

### 关键代码片段（含路径修复逻辑）
```python
import os
from docx import Document
from docx.shared import Pt, Cm
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

def create_standard_docx(filename="output.docx"):
    # 路径修复：确保在当前目录下操作，避免权限错误
    current_dir = os.getcwd()
    safe_path = os.path.join(current_dir, filename)
    
    doc = Document()

    # 1. 页面设置 (GB/T 9704 标准)
    section = doc.sections[0]
    section.top_margin = Cm(3.7)
    section.bottom_margin = Cm(3.5)
    section.left_margin = Cm(2.8)
    section.right_margin = Cm(2.6)

    # 2. 中文字体设置函数
    def set_chinese_font(run, font_name, size_pt):
        run.font.name = font_name
        run.font.size = Pt(size_pt)
        r = run._element.rPr.get_or_add_rFonts()
        r.set(qn('w:eastAsia'), font_name)

    # 3. 示例：添加标题
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("标准公文标题")
    set_chinese_font(run, '方正小标宋_GBK', 22) # 二号

    # 4. 示例：添加正文
    p = doc.add_paragraph()
    p_format = p.paragraph_format
    p_format.first_line_indent = Pt(32) # 三号字(16pt) * 2
    p_format.line_spacing = Pt(28)      # 固定值 28 磅
    p_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run = p.add_run("这是正文内容，严格遵循首行缩进和固定行距。")
    set_chinese_font(run, '仿宋_GB2312', 16) # 三号

    # 5. 安全保存
    doc.save(safe_path)
    return safe_path
```

## 注意事项
- **路径权限陷阱**：**严禁**直接使用 `/root/` 或其他系统根目录路径。这会导致 `ENOENT` 或 `Local media path is not under an allowed directory` 错误。务必使用 `os.getcwd()` 或直接使用文件名（相对路径）。
- **目录预创建**：如果保存到子目录（如 `output/report.docx`），必须先执行 `os.makedirs('output', exist_ok=True)`。
- **中文字体兼容性**：`run.font.name` 必须配合 `qn('w:eastAsia')` 使用，否则在非中文版 Word 中会回退为 Calibri。
- **字体名称**：确保环境中安装了对应字体。若不确定，优先使用通用名称如 `SimSun` (宋体), `FangSong` (仿宋), `KaiTi` (楷体)。

## 示例
**任务**：在当前环境下生成一份实验报告。
**逻辑**：
1. 获取当前目录，定义文件名为 `experiment_report.docx`。
2. 设置页面边距。
3. 写入标题（黑体，二号）和正文（仿宋，三号）。
4. 设置行间距为固定值 28 磅。
5. 保存并输出文件路径。
```python
# 示例调用
path = create_standard_docx("experiment_report.docx")
print(f"文件已成功保存至: {path}")
```