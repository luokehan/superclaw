---
name: opencli-guide
description: OpenCLI 使用指南 — Agent 通过 CLI 操作网站和应用
---

# OpenCLI 工具指南

OpenCLI 已安装在系统中，Agent 可直接调用来获取网站数据、操作桌面应用。

## 快速上手

```bash
# 列出所有可用命令
opencli list

# 获取 HackerNews 热门（无需登录）
opencli hackernews top --limit 5 -f json

# Google 搜索（无需登录）
opencli google search '人工智能最新进展' -f json
```

## 任务中的典型用法

### 信息采集任务
```bash
opencli hackernews top --limit 20 -f json > workspace/hn_top.json
opencli google news --query 'AI startup' -f json > workspace/news.json
```

### 社交媒体监控（需 Chrome 登录）
```bash
opencli twitter trending -f json > workspace/twitter_trends.json
opencli bilibili hot --limit 20 -f json > workspace/bili_hot.json
opencli xiaohongshu hot -f json > workspace/xhs_hot.json
```

### 内容下载
```bash
opencli bilibili download BV1xxxxx --output workspace/videos/
opencli twitter download elonmusk --limit 10 --output workspace/media/
```

## 输出处理

建议使用 `-f json` 输出，便于程序解析和后续处理。
