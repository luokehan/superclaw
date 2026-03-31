#!/usr/bin/env python3
"""小红书搜索+下载 — 从搜索 Pinia store 提取数据，无需打开笔记 overlay

关键发现：
  - search_result 页的 Pinia store 中 feeds._rawValue 包含完整搜索结果
  - 每条结果有 noteCard（标题/类型/图片）和 xsecToken
  - 图文笔记的图片 URL 在 noteCard.cover.urlDefault
  - 视频笔记需要打开详情页才有视频流 URL，但可以用 note ID + xsecToken 构造 URL
  - 打开视频详情后从 performance entries 获取视频 CDN URL

Usage:
  python3 xhs-search-download.py "足球教学" --pick 1 --output ./downloads
  python3 xhs-search-download.py "红烧肉" --list     # 只列出搜索结果
  python3 xhs-search-download.py "足球" --type video  # 只显示视频笔记
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request


def run_cmd(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "timeout", 1


def browser_eval(js, timeout=12):
    """Evaluate JS in browser. Uses subprocess directly to avoid shell quoting issues."""
    try:
        r = subprocess.run(
            ["openclaw", "browser", "evaluate", "--fn", js],
            capture_output=True, text=True, timeout=timeout
        )
        return r.stdout.strip()
    except subprocess.TimeoutExpired:
        return ""


def download_file(url, dest):
    try:
        req = urllib.request.Request(url, headers={
            "Referer": "https://www.xiaohongshu.com/",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as f:
            data = resp.read()
            f.write(data)
            return len(data)
    except Exception as e:
        print(f"[xhs-dl] 下载失败: {e}", file=sys.stderr)
        return 0


def search_and_extract(keyword):
    """Navigate to search page, extract results from Pinia store."""
    encoded = urllib.parse.quote(keyword)
    search_url = f"https://www.xiaohongshu.com/search_result?keyword={encoded}&source=web_search_result_notes&type=51"

    print(f"[xhs-dl] 搜索: {keyword}", file=sys.stderr)
    run_cmd(f'openclaw browser navigate "{search_url}"', timeout=30)
    time.sleep(8)

    # Scroll to load more
    browser_eval("() => { window.scrollBy(0, 800); return 1; }")
    time.sleep(3)

    # Extract from Pinia store
    js = r"""() => {
        const raw = window.__INITIAL_STATE__?.search?.feeds?._rawValue;
        if (!raw || !Array.isArray(raw)) return 'NO_DATA';
        const results = [];
        for (const item of raw) {
            const nc = item.noteCard;
            if (!nc) continue;
            const r = {
                id: item.id || '',
                token: item.xsecToken || '',
                title: nc.displayTitle || '',
                type: nc.type || 'normal',
                author: nc.user?.nickName || nc.user?.nickname || '',
                likes: nc.interactInfo?.likedCount || '0',
                cover: ''
            };
            // Get cover image URL
            if (nc.cover) {
                let url = nc.cover.urlDefault || nc.cover.url || '';
                if (url && url.startsWith('//')) url = 'https:' + url;
                r.cover = url;
            }
            results.push(r);
        }
        return JSON.stringify(results);
    }"""
    raw = browser_eval(js, timeout=15)
    if not raw or raw == 'NO_DATA':
        print(f"[xhs-dl] 搜索结果提取失败", file=sys.stderr)
        return []

    try:
        inner = raw
        if inner.startswith('"'):
            inner = json.loads(inner)
        return json.loads(inner)
    except:
        print(f"[xhs-dl] JSON 解析失败", file=sys.stderr)
        return []


def open_note_and_get_video_url(note_id, xsec_token):
    """Open note detail and extract video stream URL.
    
    Uses Vue Router push with xsecToken to open note in explore context,
    then extracts video URL from performance entries or DOM.
    WARNING: Video notes may freeze the browser. Use with caution.
    """
    print(f"[xhs-dl] 打开笔记获取视频 URL...", file=sys.stderr)

    # Use window.open to open the note in a new context
    # This avoids freezing the current search page
    note_url = f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={urllib.parse.quote(xsec_token)}&xsec_source=pc_search"

    # Navigate (will reload page)
    run_cmd(f'openclaw browser navigate "{note_url}"', timeout=25)
    time.sleep(8)

    # Try to get video URL from performance entries
    js = r"""() => {
        const entries = performance.getEntriesByType('resource');
        for (const e of entries) {
            if (e.name && e.name.includes('xhscdn') &&
                (e.name.includes('.mp4') || e.name.includes('/stream/')) &&
                !e.name.startsWith('blob:')) {
                return e.name;
            }
        }
        // Try video element
        const v = document.querySelector('video');
        if (v && v.src && !v.src.startsWith('blob:')) return v.src;
        return '';
    }"""

    vid_url = browser_eval(js, timeout=10)
    if vid_url:
        url = vid_url.strip('"')
        if url and url.startswith("http"):
            return url

    # Wait more and try again (video might still be loading)
    time.sleep(5)
    vid_url = browser_eval(js, timeout=10)
    if vid_url:
        url = vid_url.strip('"')
        if url and url.startswith("http"):
            return url

    return None


def main():
    parser = argparse.ArgumentParser(description="小红书搜索+下载")
    parser.add_argument("keyword", help="搜索关键词")
    parser.add_argument("--list", action="store_true", help="只列出搜索结果")
    parser.add_argument("--type", choices=["video", "normal", "all"], default="all", help="筛选类型")
    parser.add_argument("--pick", type=int, help="下载第 N 个结果的素材")
    parser.add_argument("--output", default="./xhs-downloads", help="输出目录")
    args = parser.parse_args()

    results = search_and_extract(args.keyword)
    if not results:
        print("搜索无结果", file=sys.stderr)
        sys.exit(1)

    # Filter by type
    if args.type != "all":
        results = [r for r in results if r["type"] == args.type]

    # List mode
    if args.list or not args.pick:
        for i, r in enumerate(results[:20], 1):
            flag = "🎬" if r["type"] == "video" else "📷"
            print(f"{i:2d}. {flag} [{r['likes']:>5s}赞] {r['title'][:35]} — {r['author']}")
        if not args.pick:
            return

    if args.pick:
        if args.pick > len(results):
            print(f"只有 {len(results)} 个结果", file=sys.stderr)
            sys.exit(1)

        picked = results[args.pick - 1]
        print(f"\n[xhs-dl] 选择: {picked['title'][:40]}", file=sys.stderr)
        print(f"[xhs-dl] 类型: {picked['type']} | 点赞: {picked['likes']}", file=sys.stderr)

        output_dir = os.path.join(args.output, picked["id"])
        os.makedirs(output_dir, exist_ok=True)

        downloaded = []

        # Download cover image
        if picked["cover"]:
            dest = os.path.join(output_dir, "cover.jpg")
            sz = download_file(picked["cover"], dest)
            if sz > 1000:
                downloaded.append({"type": "image", "path": dest, "size": sz})
                print(f"[xhs-dl] ✓ 封面 ({sz//1024}KB)", file=sys.stderr)

        # For video notes, try to get video URL
        if picked["type"] == "video" and picked.get("token"):
            vid_url = open_note_and_get_video_url(picked["id"], picked["token"])
            if vid_url:
                dest = os.path.join(output_dir, "video.mp4")
                print(f"[xhs-dl] 下载视频...", file=sys.stderr)
                sz = download_file(vid_url, dest)
                if sz > 10000:
                    downloaded.append({"type": "video", "path": dest, "size": sz})
                    print(f"[xhs-dl] ✓ 视频 ({sz//1024//1024}MB)", file=sys.stderr)
            else:
                print(f"[xhs-dl] ⚠ 无法获取视频 URL（浏览器可能冻住）", file=sys.stderr)

        # Save metadata
        meta = os.path.join(output_dir, "note.json")
        with open(meta, "w", encoding="utf-8") as f:
            json.dump(picked, f, ensure_ascii=False, indent=2)
        downloaded.append({"type": "meta", "path": meta})

        # Output
        print(json.dumps({
            "note_id": picked["id"],
            "title": picked["title"],
            "type": picked["type"],
            "author": picked["author"],
            "likes": picked["likes"],
            "downloaded": downloaded,
            "output_dir": output_dir
        }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
