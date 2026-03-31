# 小红书笔记搜索+下载+理解

## 核心工具：xhs-search-download.py

```bash
source /root/openclaw-fusion/data/.env

# 搜索并列出结果
python3 /root/openclaw-fusion/skills/gemini-video-understanding/xhs-search-download.py \
  "足球技巧" --list

# 只看视频笔记
python3 /root/openclaw-fusion/skills/gemini-video-understanding/xhs-search-download.py \
  "足球技巧" --type video --list

# 下载第 N 个结果的素材（封面图+视频）
python3 /root/openclaw-fusion/skills/gemini-video-understanding/xhs-search-download.py \
  "足球技巧" --type video --pick 1 --output ./downloads

# 下载后用 Gemini 分析
python3 /root/openclaw-fusion/skills/gemini-video-understanding/video-understand.py \
  "提取教学步骤和要点" --input ./downloads/<note-id>/video.mp4

python3 /root/openclaw-fusion/skills/gemini-video-understanding/image-understand.py \
  "描述图片内容" --input ./downloads/<note-id>/cover.jpg
```

## 工作原理

1. 导航到搜索结果页
2. 从 Pinia store 的 `search.feeds._rawValue` 提取完整搜索结果（标题/类型/作者/点赞/封面/xsecToken）
3. 下载封面图
4. 视频笔记：用 note ID + xsecToken 打开详情页，从 performance entries 获取视频 CDN URL，下载

## ⛔ 禁止

- ❌ `opencli xiaohongshu download`（xsec_token bug，永远失败）
- ❌ ffmpeg 抽帧（用 Gemini 原生视频理解）
- ❌ 旧 Gemini 模型（用 gemini-3.1-pro-preview）

## 其他工具

| 工具 | 用途 |
|------|------|
| `video-understand.py` | Gemini 视频理解（本地/YouTube/在线URL） |
| `image-understand.py` | Gemini 图片理解（单张/多张） |
| `xhs-note-reader.py` | 小红书笔记综合分析（搜索+下载+Gemini一条龙） |
| `xhs-search-download.py` | 小红书搜索+下载素材（推荐） |

所有脚本路径前缀：`/root/openclaw-fusion/skills/gemini-video-understanding/`
