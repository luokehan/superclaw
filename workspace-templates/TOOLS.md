# TOOLS.md - 本地环境配置

## ⛔ PPT 生成（最高优先级）

**做 PPT 只能用 officecli 命令行工具 + morph-ppt skill。**

**禁止使用：** pptxgenjs、python-pptx、html2pptx、html2pptx.js、SVG+cairosvg、任何 npm 包。这些方法已全部废弃删除。

**正确做法：**
1. 先完整阅读 `cat skills/morph-ppt/SKILL.md`
2. 按里面的 Phase 1-5 流程执行
3. 写 bash 脚本，用 officecli 命令 + source morph-helpers.sh
4. 运行 bash 脚本生成 .pptx

**officecli 已安装：** `/root/.local/bin/officecli` (v1.0.19)

## 已安装工具

| 工具 | 路径 | 用途 |
|------|------|------|
| officecli | /root/.local/bin/officecli | PPT/DOCX/XLSX 生成（唯一PPT工具） |
| opencli | /usr/bin/opencli | 网站操作与信息采集 |
| R | /usr/bin/Rscript | 统计分析 |
| Python3 | /usr/bin/python3 | 通用编程 |

## ⚠️ 用户上传文件（Telegram 文档下载）

**OpenClaw 不会自动下载用户通过 Telegram 发送的文档文件（.pptx/.pdf/.docx 等）。**
当用户说"我上传了文件"或"看我发的文件"时，必须用下载脚本主动拉取：

```bash
# 查看最近的文件列表
python3 /root/openclaw-fusion/skills/telegram-file-downloader.py --list

# 下载最近一个文件到 workspace
python3 /root/openclaw-fusion/skills/telegram-file-downloader.py --output /root/.openclaw/workspace/

# 下载最近3个文件
python3 /root/openclaw-fusion/skills/telegram-file-downloader.py --count 3

# 下载指定 file_id 的文件
python3 /root/openclaw-fusion/skills/telegram-file-downloader.py --file-id <file_id> --output /root/.openclaw/workspace/
```

**注意：** Telegram updates 被 gateway 消费后会清空，如果脚本找不到文件，请用户重新发送。

## JHU 学术账号

凭据：`/root/.openclaw/jhu-credentials.env`
```bash
source /root/.openclaw/jhu-credentials.env
```
