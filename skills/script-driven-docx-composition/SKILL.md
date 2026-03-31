---
name: script-driven-docx-composition
description: 通过编写并执行 Python 脚本来生成复杂的 docx 文档，支持中西文字体设置、表格自动填充、图片按比例缩放插入，适用于对格式要求极严的学术或实验报告。
version: 1.0
evolution_type: CAPTURED
---

# script-driven-docx-composition

## 适用场景
- 需要批量生成格式高度统一的学术报告、实验记录或技术文档。
- 文档包含大量重复性表格数据或需要按比例插入的实验截图。
- 对字体有严格要求（如：中文宋体，英文 Times New Roman），且常规编辑器难以快速处理中西文混排。

## 步骤
1. **环境准备**：确保环境中安装了 `python-docx` 库。
2. **初始化文档与全局样式**：创建 `Document` 对象，定义默认字体大小和行间距。
3. **实现中西文字体分离**：通过修改 `oxml` 元素，显式指定东亚字体（East Asia Font）和西文字体。
4. **自动化内容构建**：
   - 使用 `doc.add_heading()` 添加层级标题。
   - 使用 `doc.add_table()` 并通过循环填充实验数据。
   - 使用 `doc.add_picture()` 插入图片，并利用 `docx.shared.Inches` 或 `Cm` 控制尺寸。
5. **执行与验证**：运行脚本生成文件，并检查在 Word 软件中的实际渲染效果。

## 工具和命令
- **依赖库**：`pip install python-docx`
- **核心代码模式**：
  ```python
  from docx import Document
  from docx.shared import Pt, Inches
  from docx.oxml.ns import qn

  doc = Document()

  # 设置中西文分离字体的函数
  def set_font(run, font_name, east_asia_font, size_pt):
      run.font.name = font_name
      run._element.rPr.rFonts.set(qn('w:eastAsia'), east_asia_font)
      run.font.size = Pt(size_pt)

  # 插入表格
  table = doc.add_table(rows=1, cols=3)
  table.style = 'Table Grid'
  ```

## 注意事项
- **字体陷阱**：直接设置 `run.font.name` 往往只能改变西文字体。必须使用 `qn('w:eastAsia')` 才能确保中文字体（如宋体、楷体）生效。
- **图片缩放**：插入图片时，若不指定宽度或高度，图片可能会超出页面边界。建议根据页面宽度（通常 A4 除去边距约为 6 英寸）计算比例。
- **样式覆盖**：`python-docx` 的内置样式（如 'Normal'）在不同版本的 Word 中表现可能不一致，建议在脚本中显式定义关键格式。

## 示例
以下是一个生成实验报告片段的脚本示例：

```python
from docx import Document
from docx.shared import Pt, Inches
from docx.oxml.ns import qn

def create_report(output_path, data_list, img_path):
    doc = Document()
    
    # 标题
    title = doc.add_heading('实验数据分析报告', 0)
    
    # 正文段落
    p = doc.add_paragraph()
    run = p.add_run('以下是自动化生成的实验结果：')
    run.font.name = 'Times New Roman'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun') # 宋体
    
    # 表格
    table = doc.add_table(rows=1, cols=2)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = '参数'
    hdr_cells[1].text = '数值'
    
    for param, value in data_list:
        row_cells = table.add_row().cells
        row_cells[0].text = str(param)
        row_cells[1].text = str(value)
        
    # 插入图片
    doc.add_paragraph('\n实验截图：')
    doc.add_picture(img_path, width=Inches(4.5))
    
    doc.save(output_path)

# 调用示例
# create_report('report.docx', [('温度', '25C'), ('压力', '101kPa')], 'chart.png')
```