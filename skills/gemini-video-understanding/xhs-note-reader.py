#!/usr/bin/env python3
"""小红书笔记全类型阅读器 — 搜索→点击→提取→下载→Gemini分析

工作流程：
  1. 如果给的是搜索关键词 → 搜索并列出结果
  2. 如果给的是 note URL/ID → 在搜索页/feed 页找到笔记链接（带 xsec_token）→ 点击打开
  3. 从 Pinia store 提取笔记数据（文字 + 图片 URL + 视频 URL）
  4. 下载图片/视频素材
  5. Gemini 分析图片/视频内容
  6. 合并所有信息返回完整理解

支持两种模式：
  - 直接分析模式：传入 note URL 或从搜索结果页点击笔记
  - 搜索模式：传入关键词，返回笔记列表

Usage:
  # 分析笔记（从当前页面寻找并点击）
  python3 xhs-note-reader.py --url https://www.xiaohongshu.com/explore/xxxxx
  
  # 搜索后分析第 N 个结果
  python3 xhs-note-reader.py --search "红烧肉" --pick 1
  
  # 只搜索不分析
  python3 xhs-note-reader.py --search "红烧肉" --list-only
  
  # 对笔记提问
  python3 xhs-note-reader.py --url <url> --question "提取所有步骤"
  
  # 分析当前已打开的笔记弹窗
  python3 xhs-note-reader.py --current
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
import time


def load_env():
    env_path = "/root/openclaw-fusion/data/.env"
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


def run_cmd(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "timeout", 1


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


def extract_note_id(s):
    m = re.search(r'/explore/([a-f0-9]+)', s)
    if m:
        return m.group(1)
    if re.match(r'^[a-f0-9]{20,}$', s):
        return s
    return s


def download_file(url, dest):
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={
            "Referer": "https://www.xiaohongshu.com/",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as f:
            data = resp.read()
            f.write(data)
            return len(data)
    except Exception as e:
        print(f"[xhs-reader] 下载失败: {e}", file=sys.stderr)
        return 0


def search_and_list(keyword, limit=10):
    """Search XHS and return results. Try opencli first, fallback to browser DOM."""
    print(f"[xhs-reader] 搜索: {keyword}", file=sys.stderr)
    stdout, _, code = run_cmd(
        f'opencli xiaohongshu search "{keyword}" --format json --limit {limit}',
        timeout=40
    )
    if code == 0 and stdout:
        try:
            return json.loads(stdout)
        except:
            pass
    print(f"[xhs-reader] opencli 搜索失败/超时，使用浏览器搜索", file=sys.stderr)
    return []


def browser_search_and_click(keyword, pick_index=1):
    """Search on XHS explore page and click the Nth feed note.
    
    IMPORTANT: Clicking from /search_result navigates away (no overlay).
    Clicking from /explore opens the note detail overlay correctly.
    So we navigate to /explore first, then click from the feed.
    """
    # Navigate to explore (the only page where clicking opens overlay)
    print(f"[xhs-reader] 打开 explore 页面...", file=sys.stderr)
    run_cmd('openclaw browser navigate "https://www.xiaohongshu.com/explore"', timeout=20)
    time.sleep(6)

    # Click the Nth note on the explore feed
    js = f"""() => {{
        const items = document.querySelectorAll('section.note-item a[href*="/explore/"]');
        const unique = [];
        const seen = new Set();
        for (const a of items) {{
            const href = a.href.split('?')[0];
            if (!seen.has(href) && a.href.includes('xsec_token')) {{
                seen.add(href);
                unique.push(a);
            }}
        }}
        const idx = {pick_index - 1};
        if (idx < unique.length) {{
            const a = unique[idx];
            const title = a.closest('section')?.querySelector('.title, .note-title')?.textContent || '';
            a.click();
            return 'clicked|' + title.trim().substring(0, 40) + '|' + a.href.substring(0, 80);
        }}
        return 'not_found|count:' + unique.length;
    }}"""
    result = browser_eval(js, timeout=10)
    if result and 'clicked' in result:
        parts = result.strip('"').split('|')
        title = parts[1] if len(parts) > 1 else ''
        print(f"[xhs-reader] ✓ 点击第 {pick_index} 个: {title}", file=sys.stderr)
        time.sleep(5)
        return True
    print(f"[xhs-reader] explore 页面点击失败: {result}", file=sys.stderr)
    return False


def click_note_on_page(note_id):
    """Try to find and click a note link on the current page."""
    js = f"""() => {{
        const links = document.querySelectorAll('a[href*="{note_id}"]');
        for (const a of links) {{
            if (a.href.includes('xsec_token') || a.href.includes('{note_id}')) {{
                a.click();
                return 'clicked';
            }}
        }}
        return 'not_found';
    }}"""
    result = browser_eval(js)
    return 'clicked' in result


def open_note_via_search(note_id, keyword=None):
    """Open note by navigating to search/explore page and clicking the note link.
    
    Strategy order:
    1. If keyword given → navigate to search results → click note
    2. Check if already on a page with the note link → click
    3. Navigate to explore → click any note with matching ID
    4. Direct navigate (last resort, may not load due to xsec_token)
    """

    # Strategy 1: Search page with keyword
    if keyword:
        import urllib.parse
        search_url = f"https://www.xiaohongshu.com/search_result?keyword={urllib.parse.quote(keyword)}&source=web_search_result_notes&type=51"
        print(f"[xhs-reader] 导航到搜索页: {keyword}", file=sys.stderr)
        run_cmd(f'openclaw browser navigate "{search_url}"', timeout=20)
        time.sleep(5)

        # Scroll to load more
        browser_eval("() => { window.scrollBy(0, 800); return 1; }")
        time.sleep(2)
        browser_eval("() => { window.scrollBy(0, 800); return 1; }")
        time.sleep(2)

        if click_note_on_page(note_id):
            print(f"[xhs-reader] ✓ 在搜索结果中点击了笔记", file=sys.stderr)
            time.sleep(4)
            return True
        print(f"[xhs-reader] 搜索页未找到笔记 {note_id[:12]}...", file=sys.stderr)

    # Strategy 2: Check current page
    if click_note_on_page(note_id):
        print(f"[xhs-reader] ✓ 在当前页面点击了笔记", file=sys.stderr)
        time.sleep(4)
        return True

    # Strategy 3: Explore page
    print(f"[xhs-reader] 尝试从首页打开...", file=sys.stderr)
    run_cmd('openclaw browser navigate "https://www.xiaohongshu.com/explore"', timeout=15)
    time.sleep(4)

    if click_note_on_page(note_id):
        print(f"[xhs-reader] ✓ 在首页点击了笔记", file=sys.stderr)
        time.sleep(4)
        return True

    # Strategy 4: Direct navigate (xsec_token missing, might partially load)
    print(f"[xhs-reader] ⚠ 直接导航（可能不完整）...", file=sys.stderr)
    run_cmd(f'openclaw browser navigate "https://www.xiaohongshu.com/explore/{note_id}"', timeout=15)
    time.sleep(5)
    return True


def extract_note_data():
    """Extract note data from DOM of the note detail overlay.
    
    Vue 3 Pinia store uses reactive proxies that block property access from evaluate(),
    so we extract everything from the rendered DOM instead.
    """
    # Extract text + images from DOM
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

        // Collect unique image URLs from swiper slides
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

        // Check for video
        const vid = nc.querySelector('video');
        if (vid) {
            r.type = 'video';
            if (vid.src && !vid.src.startsWith('blob:')) {
                r.videos.push(vid.src);
            }
        }

        // Also check for xgplayer or other video containers
        if (nc.querySelector('.player-container, .xg-video-container, [class*=video-player]')) {
            r.type = 'video';
        }

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

    # For video notes: if we only got blob: URL, try to get real video URL
    # from performance entries (network requests) or page source
    if result["type"] == "video" and not result["videos"]:
        js_perf = r"""() => {
            const entries = performance.getEntriesByType('resource');
            for (const e of entries) {
                if (e.name && (e.name.includes('.mp4') || e.name.includes('stream'))
                    && e.name.includes('xhscdn') && !e.name.startsWith('blob:')) {
                    return e.name;
                }
            }
            // Try from page source
            const scripts = document.querySelectorAll('script');
            for (const s of scripts) {
                const t = s.textContent || '';
                const m = t.match(/masterUrl['":\s]+(https?:\/\/[^'"]+\.mp4[^'"]*)/);
                if (m) return m[1];
                const m2 = t.match(/(https?:\/\/sns-video[^'"]+\.mp4[^'"]*)/);
                if (m2) return m2[1];
            }
            return '';
        }"""
        vid_raw = browser_eval(js_perf, timeout=10)
        if vid_raw:
            url = vid_raw.strip('"')
            if url and url.startswith("http"):
                result["videos"] = [url]

    if result["title"] or result["images"] or result["videos"]:
        return result
    return None


def take_screenshot(output_path):
    """Fallback: take a screenshot of the current page."""
    run_cmd('openclaw browser screenshot', timeout=10)
    time.sleep(1)
    media_dir = os.path.expanduser("~/.openclaw/media/browser/")
    if os.path.isdir(media_dir):
        files = sorted(
            glob.glob(os.path.join(media_dir, "*.jpg")) + glob.glob(os.path.join(media_dir, "*.png")),
            key=os.path.getmtime, reverse=True
        )
        if files:
            import shutil
            shutil.copy2(files[0], output_path)
            return output_path
    return None


def gemini_analyze(prompt, image_paths=None, video_path=None, model="gemini-3.1-pro-preview"):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "[GEMINI_API_KEY not set]"

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    parts = []

    if image_paths:
        for p in image_paths[:10]:
            try:
                data = open(p, "rb").read()
                ext = os.path.splitext(p)[1].lower()
                mime = {".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")
                parts.append(types.Part(inline_data=types.Blob(data=data, mime_type=mime)))
            except Exception as e:
                print(f"[xhs-reader] 图片加载失败 {p}: {e}", file=sys.stderr)

    if video_path:
        file_size = os.path.getsize(video_path)
        if file_size < 20 * 1024 * 1024:
            data = open(video_path, "rb").read()
            parts.append(types.Part(inline_data=types.Blob(data=data, mime_type="video/mp4")))
        else:
            print(f"[xhs-reader] 上传视频 ({file_size // 1024 // 1024}MB)...", file=sys.stderr)
            upload_path = video_path
            try:
                video_path.encode("ascii")
            except UnicodeEncodeError:
                import shutil as _s, tempfile as _t
                _f = _t.NamedTemporaryFile(suffix=".mp4", delete=False)
                _f.close()
                _s.copy2(video_path, _f.name)
                upload_path = _f.name
            uploaded = client.files.upload(file=upload_path)
            if upload_path != video_path:
                os.unlink(upload_path)
            for _ in range(120):
                f = client.files.get(name=uploaded.name)
                if f.state.name == "ACTIVE":
                    parts.append(types.Part(file_data=types.FileData(file_uri=f.uri, mime_type="video/mp4")))
                    break
                if f.state.name == "FAILED":
                    return "[视频处理失败]"
                time.sleep(3)

    parts.append(types.Part(text=prompt))

    response = client.models.generate_content(
        model=model,
        contents=types.Content(parts=parts),
    )
    return response.text or ""


def main():
    parser = argparse.ArgumentParser(description="小红书笔记全类型阅读器")
    parser.add_argument("--url", help="笔记 URL 或 note ID")
    parser.add_argument("--search", help="搜索关键词")
    parser.add_argument("--pick", type=int, help="选择搜索结果中第 N 个笔记分析")
    parser.add_argument("--list-only", action="store_true", help="只列出搜索结果不分析")
    parser.add_argument("--current", action="store_true", help="分析当前已打开的笔记弹窗")
    parser.add_argument("--question", help="对笔记内容提问")
    parser.add_argument("--output", help="保存结果到文件")
    parser.add_argument("--model", default="gemini-3.1-pro-preview", help="Gemini 模型")
    # Legacy positional arg support
    parser.add_argument("note", nargs="?", help="笔记 URL 或 note ID（兼容旧用法）")
    args = parser.parse_args()

    load_env()

    # Handle legacy positional arg
    if args.note and not args.url:
        args.url = args.note

    # Mode 1: Search only
    if args.search and args.list_only:
        results = search_and_list(args.search)
        if results:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print("搜索无结果")
        return

    # Mode 2: Search + pick — directly click in browser search page
    if args.search and args.pick:
        if not browser_search_and_click(args.search, args.pick):
            print(f"[xhs-reader] 浏览器点击失败，尝试 opencli 搜索...", file=sys.stderr)
            results = search_and_list(args.search)
            if not results or args.pick > len(results):
                print(f"搜索结果不足 {args.pick} 个", file=sys.stderr)
                sys.exit(1)
            picked = results[args.pick - 1]
            note_id = extract_note_id(picked.get("url", ""))
            print(f"[xhs-reader] 选择第 {args.pick} 个: {picked.get('title', '?')}", file=sys.stderr)
            open_note_via_search(note_id, keyword=args.search)
        note_id = "search_pick"  # placeholder for output

    # Mode 3: Direct URL
    elif args.url:
        note_id = extract_note_id(args.url)
        print(f"[xhs-reader] 笔记 ID: {note_id}", file=sys.stderr)
        open_note_via_search(note_id)

    # Mode 4: Current page
    elif args.current:
        print(f"[xhs-reader] 分析当前页面...", file=sys.stderr)

    else:
        parser.print_help()
        return

    # Extract note data
    print(f"[xhs-reader] 提取笔记数据...", file=sys.stderr)
    data = extract_note_data()

    if not data:
        time.sleep(3)
        data = extract_note_data()

    with tempfile.TemporaryDirectory() as tmpdir:
        text_content = data.get("text", "") if data else ""
        title = data.get("title", "") if data else ""
        author = data.get("author", "") if data else ""
        note_type = data.get("type", "unknown") if data else "unknown"
        image_analysis = ""
        video_analysis = ""

        if data and (data.get("images") or data.get("videos")):
            # Download and analyze images
            if data.get("images"):
                img_dir = os.path.join(tmpdir, "images")
                os.makedirs(img_dir, exist_ok=True)
                img_paths = []
                for i, url in enumerate(data["images"][:10]):
                    ext = ".webp" if ".webp" in url else ".jpg"
                    dest = os.path.join(img_dir, f"img_{i}{ext}")
                    sz = download_file(url, dest)
                    if sz > 1000:
                        img_paths.append(dest)
                        print(f"[xhs-reader] ✓ 图片 {i+1} ({sz//1024}KB)", file=sys.stderr)

                if img_paths:
                    print(f"[xhs-reader] Gemini 分析 {len(img_paths)} 张图片...", file=sys.stderr)
                    image_analysis = gemini_analyze(
                        "请详细描述这些图片的内容。如果是教程/攻略类图片，提取其中的关键步骤和信息。如果有文字，请提取文字内容。用中文回答。",
                        image_paths=img_paths,
                        model=args.model
                    )

            # Download and analyze video
            if data.get("videos"):
                vid_dir = os.path.join(tmpdir, "video")
                os.makedirs(vid_dir, exist_ok=True)
                vid_path = os.path.join(vid_dir, "video.mp4")
                print(f"[xhs-reader] 下载视频...", file=sys.stderr)
                sz = download_file(data["videos"][0], vid_path)
                if sz > 10000:
                    print(f"[xhs-reader] Gemini 分析视频 ({sz//1024//1024}MB)...", file=sys.stderr)
                    video_analysis = gemini_analyze(
                        "请详细描述这个视频的内容：1) 视频主题和场景 2) 关键步骤/信息 3) 语音/对话内容（如果有）4) 视觉细节。用中文回答。",
                        video_path=vid_path,
                        model=args.model
                    )
        else:
            # No data from Pinia store — fallback to screenshot
            print(f"[xhs-reader] 无法提取数据，使用截图分析...", file=sys.stderr)
            ss_path = os.path.join(tmpdir, "screenshot.jpg")
            if take_screenshot(ss_path):
                image_analysis = gemini_analyze(
                    "这是一个小红书笔记页面的截图。请完整提取并描述：1) 标题 2) 作者 3) 完整文字 4) 图片描述 5) 互动数据。用中文回答。",
                    image_paths=[ss_path],
                    model=args.model
                )

        # Synthesize
        combined = f"标题: {title}\n作者: {author}\n类型: {note_type}\n\n"
        if text_content:
            combined += f"【笔记文字】\n{text_content}\n\n"
        if image_analysis:
            combined += f"【图片内容】\n{image_analysis}\n\n"
        if video_analysis:
            combined += f"【视频内容】\n{video_analysis}\n\n"

        if args.question:
            prompt = f"基于以下小红书笔记的完整内容，回答问题。\n\n{combined}\n问题: {args.question}"
        else:
            prompt = f"基于以下小红书笔记的完整内容，给出全面准确的总结，包含关键信息。\n\n{combined}"

        print(f"[xhs-reader] 生成综合理解...", file=sys.stderr)
        final = gemini_analyze(prompt, model=args.model)

        result = f"---\n**笔记**: https://www.xiaohongshu.com/explore/{note_id if 'note_id' in dir() else '?'}\n"
        result += f"**标题**: {title}\n**作者**: {author}\n**类型**: {note_type}\n---\n\n"
        if text_content:
            result += f"## 笔记原文\n{text_content}\n\n"
        if image_analysis:
            result += f"## 图片理解\n{image_analysis}\n\n"
        if video_analysis:
            result += f"## 视频理解\n{video_analysis}\n\n"
        result += f"## 综合分析\n{final}\n"

        if args.output:
            os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"[xhs-reader] 已保存: {args.output}", file=sys.stderr)
        else:
            print(result)


if __name__ == "__main__":
    main()
