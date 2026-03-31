---
name: chinese-standard-docx-styling-enhanced
description: 在标准中国公文排版基础上，增加了数据一致性自审机制，确保生成的文档中关键数值、引用和元数据与源数据完全一致。
version: 1.1
evolved_from: chinese-standard-docx-styling
evolution_type: DERIVED
---

# Skill 名称：chinese-standard-docx-styling-enhanced

## 适用场景
适用于生成对排版格式有严格要求（如中国公文、学术论文、专业技术报告），且包含大量关键实验数据（如比活、Km值）、统计数值或复杂引用的文档。该技能在排版基础上强化了数据准确性校验，防止在自动化生成或重写过程中引入人为偏差。

## 步骤
1. **环境准备**：安装 `python-docx` 库。
2. **建立数据源真相（Source of Truth）**：在生成文档前，将所有关键数值、作者信息、图表编号提取为结构化字典或 JSON，作为审计基准。
3. **初始化文档与页面设置**：设置 A4 纸张及标准公文页边距（上 3.7cm, 下 3.5cm, 左 2.8cm, 右 2.6cm）。
4. **全局样式与中文字体处理**：使用 `qn` 模块设置 `w:eastAsia` 属性，确保中文字体（仿宋、黑体等）在所有 Word 版本中正确显示。
5. **内容注入与格式化**：
    - 使用占位符或模板逻辑注入数据。
    - 设置首行缩进（2 字符）、固定行间距（28-30 磅）。
6. **数据一致性自审（核心增强）**：
    - 遍历生成的 `doc` 对象，提取所有数值和关键术语。
    - 与步骤 2 的数据源进行双向比对。
    - 验证图表引用编号是否连续且与正文对应。
7. **保存与验证报告**：保存文档并输出一份简要的数据一致性校验报告。

## 工具和命令
### 核心依赖
```bash
pip install python-docx
```

### 增强版代码片段（含审计逻辑）
```python
from docx import Document
from docx.shared import Pt, Cm
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

# 1. 定义源数据 (Source of Truth)
source_data = {
    "specific_activity": "152.5 U/mg",
    "km_value": "0.045 mM",
    "author": "张三",
    "report_no": "2023-TECH-001"
}

def set_chinese_font(run, font_name, size_pt):
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    r = run._element.rPr.rFonts
    r.set(qn('w:eastAsia'), font_name)

doc = Document()

# 2. 注入数据并排版
p = doc.add_paragraph()
p.paragraph_format.first_line_indent = Pt(32)
p.paragraph_format.line_spacing = Pt(28)
run = p.add_run(f"经检测，该酶的比活为 {source_data['specific_activity']}，其 Km 值为 {source_data['km_value']}。")
set_chinese_font(run, '仿宋_GB2312', 16)

# 3. 数据一致性自审函数
def audit_document(doc, source_dict):
    full_text = "".join([p.text for p in doc.paragraphs])
    missing_data = []
    for key, value in source_dict.items():
        if value not in full_text:
            missing_data.append(f"缺失数据: {key} -> {value}")
    
    if not missing_data:
        print("✅ 数据一致性审计通过：所有关键数值已正确写入。")
    else:
        print("❌ 审计失败：")
        for error in missing_data:
            print(error)

# 执行审计
audit_document(doc, source_data)
doc.save("Enhanced_Report.docx")
```

## 注意事项
- **浮点数精度陷阱**：在比对数值时，注意字符串格式化导致的精度差异（如 `0.045` vs `0.0450`），建议在 `source_data` 中统一使用字符串。
- **单位一致性**：确保源数据中的单位（如 `U/mg`）与文档描述中的单位完全匹配。
- **字体名称准确性**：Windows 系统通常为 `仿宋` 或 `楷体`，老旧系统可能需要 `仿宋_GB2312`。
- **图表自动编号**：若涉及大量图表，建议维护一个计数器，在审计阶段检查 `图 1` 到 `图 N` 的连续性。

## 示例
**任务**：生成一份包含实验数据的技术报告。
**逻辑**：
1. **数据源**：定义 `Km=0.8mM`, `Vmax=120umol/min`。
2. **排版**：标题二号黑体居中，正文三号仿宋，行距 28 磅。
3. **审计**：在保存前扫描全文，确认 `0.8mM` 和 `120umol/min` 字符串是否存在。
4. **输出**：若审计发现 `0.8` 被误写为 `0.08`，则抛出异常或标记警告。