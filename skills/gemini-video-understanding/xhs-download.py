#!/usr/bin/env python3
"""小红书笔记素材下载器 — 通过点击笔记链接打开详情（绕过 xsec_token 限制）

opencli xiaohongshu download 因 xsec_token 问题无法打开笔记详情页。
本脚本通过搜索页/feed 页点击笔记链接打开带 token 的详情弹窗，
然后从 Pinia store 提取媒体 URL 下载。

Usage:
  python3 xhs-download.py <note-id-or-url> [--output dir]
  python3 xhs-download.py <note-id-or-url> --search-keyword "红烧肉"
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request


def run_cmd(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "timeout", 1


def extract_note_id(s):
    m = re.search(r'/explore/([a-f0-9]+)', s)
    if m:
        return m.group(1)
    if re.match(r'^[a-f0-9]{20,}$', s):
        return s
    return s


def download_file(url, dest, referer="https://www.xiaohongshu.com/"):
    try:
        req = urllib.request.Request(url, headers={
            "Referer": referer,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as f:
            data = resp.read()
            f.write(data)
            return len(data)
    except Exception as e:
        print(f"[xhs-dl] 下载失败 {os.path.basename(dest)}: {e}", file=sys.stderr)
        return 0


def browser_eval(js, timeout=12):
    """Evaluate JS in browser. Uses subprocess list form to avoid shell quoting issues."""
    try:
        r = subprocess.run(
            ["openclaw", "browser", "evaluate", "--fn", js],
            capture_output=True, text=True, timeout=timeout
        )
        return r.stdout.strip()
    except subprocess.TimeoutExpired:
        return ""


def open_note_via_click(note_id):
    """Open note detail by clicking its link from feed/search page (which has xsec_token)."""

    # Step 1: Make sure we're on the XHS explore page
    print(f"[xhs-dl] 确保在小红书首页...", file=sys.stderr)
    run_cmd('openclaw browser navigate "https://www.xiaohongshu.com/explore"', timeout=15)
    time.sleep(4)

    # Step 2: Check if the note is visible on current page
    js_find = f"""() => {{
        const links = document.querySelectorAll('a[href*="{note_id}"]');
        if (links.length > 0) {{
            links[0].click();
            return 'clicked';
        }}
        return 'not_found';
    }}"""
    result = browser_eval(js_find)

    if 'clicked' in result:
        print(f"[xhs-dl] 在首页找到并点击了笔记", file=sys.stderr)
        time.sleep(4)
        return True

    # Step 3: If not found, try scrolling and looking
    print(f"[xhs-dl] 首页未找到笔记，尝试搜索...", file=sys.stderr)

    # Navigate to search with a generic query to find the note
    search_url = f"https://www.xiaohongshu.com/search_result?keyword=&source=web_search_result_notes"
    run_cmd(f'openclaw browser navigate "https://www.xiaohongshu.com/explore/{note_id}"', timeout=15)
    time.sleep(5)

    # Even without xsec_token, the page might partially load with __INITIAL_STATE__
    return True


def extract_note_data():
    """Extract note data from DOM of the note detail overlay."""
    js_dom = r"""() => {
        const nc = document.querySelector('.note-container');
        if (!nc) return 'NO_CONTAINER';
        const r = {title:'', text:'', author:'', images:[], videos:[], type:'image'};
        const author = nc.querySelector('.username');
        r.author = author?.textContent?.trim() || '';
        const title = nc.querySelector('#detail-title, .title');
        r.title = title?.textContent?.trim() || '';
        const desc = nc.querySelector('#detail-desc, .desc, .note-text');
        r.text = desc?.textContent?.trim() || '';
        const seen = new Set();
        nc.querySelectorAll('.swiper-slide img, .note-image img, img').forEach(img => {
            const src = img.src || '';
            const key = src.split('?')[0];
            if (src.includes('xhscdn') && !src.includes('avatar') && !src.includes('emoji')
                && img.width > 50 && !seen.has(key)) {
                seen.add(key);
                r.images.push(key);
            }
        });
        const vid = nc.querySelector('video');
        if (vid) {
            r.type = 'video';
            if (vid.src && !vid.src.startsWith('blob:')) r.videos.push(vid.src);
        }
        if (nc.querySelector('.player-container, .xg-video-container, [class*=video-player]')) r.type = 'video';
        return JSON.stringify(r);
    }"""
    raw = browser_eval(js_dom, timeout=10)
    if not raw or raw == 'NO_CONTAINER':
        return None
    try:
        inner = raw
        if inner.startswith('"'):
            inner = json.loads(inner)
        result = json.loads(inner)
    except:
        return None

    if result.get("type") == "video" and not result.get("videos"):
        js_perf = r"""() => {
            const entries = performance.getEntriesByType('resource');
            for (const e of entries) {
                if (e.name && (e.name.includes('.mp4') || e.name.includes('stream'))
                    && e.name.includes('xhscdn') && !e.name.startsWith('blob:')) return e.name;
            }
            const scripts = document.querySelectorAll('script');
            for (const s of scripts) {
                const t = s.textContent || '';
                const m = t.match(/(https?:\/\/sns-video[^'"]+\.mp4[^'"]*)/);
                if (m) return m[1];
            }
            return '';
        }"""
        vid_raw = browser_eval(js_perf, timeout=10)
        if vid_raw:
            url = vid_raw.strip('"')
            if url and url.startswith("http"):
                result["videos"] = [url]

    if result.get("title") or result.get("images") or result.get("videos"):
        return result
    return None


def main():
    parser = argparse.ArgumentParser(description="小红书笔记素材下载")
    parser.add_argument("note", help="笔记 URL 或 note ID")
    parser.add_argument("--output", default="./xhs-downloads", help="输出目录")
    args = parser.parse_args()

    note_id = extract_note_id(args.note)
    output_dir = os.path.join(args.output, note_id)
    os.makedirs(output_dir, exist_ok=True)

    print(f"[xhs-dl] 笔记 ID: {note_id}", file=sys.stderr)
    print(f"[xhs-dl] 输出目录: {output_dir}", file=sys.stderr)

    # Open note
    open_note_via_click(note_id)

    # Extract data
    print(f"[xhs-dl] 提取笔记数据...", file=sys.stderr)
    data = extract_note_data()

    # Retry once if empty
    if not data:
        print(f"[xhs-dl] 首次提取失败，等待后重试...", file=sys.stderr)
        time.sleep(5)
        data = extract_note_data()

    if not data:
        print(f"[xhs-dl] ❌ 无法提取笔记数据", file=sys.stderr)
        print(json.dumps({"note_id": note_id, "error": "无法提取数据", "downloaded": []}, ensure_ascii=False))
        sys.exit(1)

    print(f"[xhs-dl] 标题: {data.get('title', '?')[:40]}", file=sys.stderr)
    print(f"[xhs-dl] 图片: {len(data.get('images', []))}张", file=sys.stderr)
    print(f"[xhs-dl] 视频: {len(data.get('videos', []))}个", file=sys.stderr)

    downloaded = []

    # Download images
    for i, url in enumerate(data.get("images", [])[:20]):
        if not url:
            continue
        ext = ".webp" if ".webp" in url else ".png" if ".png" in url else ".jpg"
        dest = os.path.join(output_dir, f"image_{i+1:02d}{ext}")
        size = download_file(url, dest)
        if size > 1000:
            downloaded.append({"type": "image", "path": dest, "size": size})
            print(f"[xhs-dl] ✓ image_{i+1:02d}{ext} ({size//1024}KB)", file=sys.stderr)

    # Download videos
    for i, url in enumerate(data.get("videos", [])[:3]):
        if not url:
            continue
        dest = os.path.join(output_dir, f"video_{i+1:02d}.mp4")
        print(f"[xhs-dl] 下载视频中...", file=sys.stderr)
        size = download_file(url, dest)
        if size > 10000:
            downloaded.append({"type": "video", "path": dest, "size": size})
            print(f"[xhs-dl] ✓ video_{i+1:02d}.mp4 ({size//1024//1024}MB)", file=sys.stderr)

    # Save text
    text = data.get("text", "")
    title = data.get("title", "")
    if text or title:
        meta_path = os.path.join(output_dir, "note.txt")
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(f"标题: {title}\n作者: {data.get('author', '')}\n\n{text}")
        downloaded.append({"type": "text", "path": meta_path, "size": os.path.getsize(meta_path)})

    # Output JSON
    result = {
        "note_id": note_id,
        "title": title,
        "author": data.get("author", ""),
        "type": data.get("type", "unknown"),
        "text": text,
        "downloaded": downloaded,
        "output_dir": output_dir
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
