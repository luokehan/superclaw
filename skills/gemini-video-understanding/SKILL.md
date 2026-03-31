# Gemini 多模态理解工具集

模型：**gemini-3.1-pro-preview**（最新最强，勿用旧模型）

本目录包含三个工具，覆盖所有多模态理解场景：

| 工具 | 用途 |
|------|------|
| `video-understand.py` | 视频理解（本地文件/YouTube/在线URL） |
| `image-understand.py` | 图片理解（单张/多张） |
| `xhs-note-reader.py` | 小红书笔记一键理解（自动处理文字+图片+视频） |

## ⛔ 规则

- **遇到视频 → 用 video-understand.py**，不要用 ffmpeg 抽帧
- **遇到图片 → 用 image-understand.py**，不要只描述文件名
- **遇到小红书笔记 → 用 xhs-note-reader.py**，不要手动截图
- 所有工具默认使用 `gemini-3.1-pro-preview`，**禁止降级到旧模型**

---

## 1. video-understand.py — 视频理解

```bash
source /root/openclaw-fusion/data/.env

# 本地视频
python3 /root/openclaw-fusion/skills/gemini-video-understanding/video-understand.py \
  "总结视频内容" --input video.mp4

# YouTube（直传 URL，无需下载）
python3 /root/openclaw-fusion/skills/gemini-video-understanding/video-understand.py \
  "这个视频讲了什么" --input https://www.youtube.com/watch?v=xxxxx

# 裁剪+高帧率
python3 /root/openclaw-fusion/skills/gemini-video-understanding/video-understand.py \
  "分析动作" --input video.mp4 --start 10 --end 30 --fps 5

# 长视频省 token
python3 /root/openclaw-fusion/skills/gemini-video-understanding/video-understand.py \
  "总结讲座" --input lecture.mp4 --fps 0.5 --low-res

# 保存结果
python3 /root/openclaw-fusion/skills/gemini-video-understanding/video-understand.py \
  "描述内容" --input video.mp4 --output result.md
```

参数：`--start/--end`（裁剪秒数）、`--fps`（帧率）、`--low-res`（省token）、`--output`

支持格式：mp4, mpeg, mov, avi, flv, webm, wmv, 3gpp

---

## 2. image-understand.py — 图片理解

```bash
source /root/openclaw-fusion/data/.env

# 单张图片
python3 /root/openclaw-fusion/skills/gemini-video-understanding/image-understand.py \
  "描述这张图片" --input photo.jpg

# 多张图片一起分析
python3 /root/openclaw-fusion/skills/gemini-video-understanding/image-understand.py \
  "对比这几张图片的区别" --input img1.png img2.png img3.png

# 通配符批量
python3 /root/openclaw-fusion/skills/gemini-video-understanding/image-understand.py \
  "提取所有图中的文字和步骤" --input ./downloads/*.jpg

# 保存结果
python3 /root/openclaw-fusion/skills/gemini-video-understanding/image-understand.py \
  "分析产品" --input product.jpg --output analysis.md
```

支持格式：jpg, png, webp, gif（最多 20 张）

---

## 3. xhs-note-reader.py — 小红书笔记一键理解

```bash
source /root/openclaw-fusion/data/.env

# 一键理解（自动识别图文/视频）
python3 /root/openclaw-fusion/skills/gemini-video-understanding/xhs-note-reader.py \
  https://www.xiaohongshu.com/explore/<note-id>

# 提问
python3 /root/openclaw-fusion/skills/gemini-video-understanding/xhs-note-reader.py \
  <note-url-or-id> --question "推荐了什么产品？"

# 保存
python3 /root/openclaw-fusion/skills/gemini-video-understanding/xhs-note-reader.py \
  <note-url-or-id> --output analysis.md
```

工作原理：截图→Gemini视觉提取文字和图片→检测视频→下载→Gemini视频理解→综合

---

## Token 消耗

| 内容 | 默认 | 低分辨率 |
|------|------|----------|
| 视频每秒 | ~300 token | ~100 token |
| 1分钟视频 | ~18K | ~6K |
| 10分钟视频 | ~180K | ~60K |
| 单张图片 | ~258 token | ~66 token |
