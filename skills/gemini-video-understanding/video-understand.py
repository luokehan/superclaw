#!/usr/bin/env python3
"""Gemini 视频理解工具 — 本地文件 / YouTube URL / 在线 URL

支持三种输入：
  1. 本地视频文件（通过 File API 上传，支持大文件到 2GB）
  2. YouTube URL（直接传给 Gemini，无需下载）
  3. 在线视频 URL（先下载到临时文件再上传）

Usage:
  python3 video-understand.py "总结这个视频" --input video.mp4
  python3 video-understand.py "这个视频讲了什么" --input https://www.youtube.com/watch?v=xxx
  python3 video-understand.py "提取关键信息" --input https://example.com/video.mp4
  python3 video-understand.py "00:30处发生了什么" --input video.mp4 --start 20 --end 60
  python3 video-understand.py "描述视频内容" --input video.mp4 --fps 2
  python3 video-understand.py "总结" --input video.mp4 --output summary.md
"""
import argparse
import os
import sys
import time
import tempfile
import re


def is_youtube_url(url):
    return bool(re.match(r'https?://(www\.)?(youtube\.com|youtu\.be)/', url))


def is_url(s):
    return s.startswith("http://") or s.startswith("https://")


def download_url(url, dest):
    import urllib.request
    print(f"[gemini-video] 下载中: {url}", file=sys.stderr)
    urllib.request.urlretrieve(url, dest)
    size = os.path.getsize(dest)
    print(f"[gemini-video] 下载完成: {size / 1024 / 1024:.1f} MB", file=sys.stderr)
    return dest


def wait_for_processing(client, file_ref, timeout=600):
    """Poll until file is ACTIVE (processed)."""
    start = time.time()
    while time.time() - start < timeout:
        f = client.files.get(name=file_ref.name)
        if f.state.name == "ACTIVE":
            return f
        if f.state.name == "FAILED":
            print(f"ERROR: File processing failed: {f.state}", file=sys.stderr)
            sys.exit(1)
        print(f"[gemini-video] 处理中... ({f.state.name})", file=sys.stderr)
        time.sleep(5)
    print("ERROR: File processing timed out", file=sys.stderr)
    sys.exit(1)


def guess_mime(path):
    ext = os.path.splitext(path)[1].lower()
    return {
        ".mp4": "video/mp4", ".mpeg": "video/mpeg", ".mov": "video/mov",
        ".avi": "video/avi", ".flv": "video/x-flv", ".mpg": "video/mpg",
        ".webm": "video/webm", ".wmv": "video/wmv", ".3gp": "video/3gpp",
    }.get(ext, "video/mp4")


def main():
    parser = argparse.ArgumentParser(description="Gemini Video Understanding")
    parser.add_argument("prompt", help="提问内容（如：总结这个视频）")
    parser.add_argument("--input", required=True, help="视频路径、YouTube URL 或在线视频 URL")
    parser.add_argument("--output", help="保存结果到文件（默认输出到 stdout）")
    parser.add_argument("--model", default="gemini-3.1-pro-preview", help="模型名称")
    parser.add_argument("--start", type=int, help="裁剪起始秒数")
    parser.add_argument("--end", type=int, help="裁剪结束秒数")
    parser.add_argument("--fps", type=float, help="自定义帧率（默认 1fps，长视频可设 0.5，快动作设 2-5）")
    parser.add_argument("--low-res", action="store_true", help="低分辨率模式（节省 token，66 token/帧 vs 258）")
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        from dotenv import load_dotenv
        load_dotenv("/root/openclaw-fusion/data/.env")
        api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    video_metadata_kwargs = {}
    if args.start is not None or args.end is not None:
        if args.start is not None:
            video_metadata_kwargs["start_offset"] = f"{args.start}s"
        if args.end is not None:
            video_metadata_kwargs["end_offset"] = f"{args.end}s"
    if args.fps:
        video_metadata_kwargs["fps"] = args.fps

    video_metadata = types.VideoMetadata(**video_metadata_kwargs) if video_metadata_kwargs else None

    gen_config = {}
    if args.low_res:
        gen_config["media_resolution"] = "low"

    input_src = args.input
    parts = []
    tmp_file = None

    if is_youtube_url(input_src):
        print(f"[gemini-video] YouTube 模式: {input_src}", file=sys.stderr)
        part_kwargs = {"file_data": types.FileData(file_uri=input_src)}
        if video_metadata:
            part_kwargs["video_metadata"] = video_metadata
        parts.append(types.Part(**part_kwargs))

    elif is_url(input_src):
        ext = os.path.splitext(input_src.split("?")[0])[1] or ".mp4"
        tmp_file = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        download_url(input_src, tmp_file.name)
        input_src = tmp_file.name

        print(f"[gemini-video] 上传文件: {input_src}", file=sys.stderr)
        uploaded = client.files.upload(file=input_src)
        uploaded = wait_for_processing(client, uploaded)
        print(f"[gemini-video] 文件已就绪: {uploaded.uri}", file=sys.stderr)

        part_kwargs = {"file_data": types.FileData(file_uri=uploaded.uri, mime_type=guess_mime(input_src))}
        if video_metadata:
            part_kwargs["video_metadata"] = video_metadata
        parts.append(types.Part(**part_kwargs))

    else:
        if not os.path.exists(input_src):
            print(f"ERROR: File not found: {input_src}", file=sys.stderr)
            sys.exit(1)

        file_size = os.path.getsize(input_src)
        print(f"[gemini-video] 本地文件: {input_src} ({file_size / 1024 / 1024:.1f} MB)", file=sys.stderr)

        if file_size < 20 * 1024 * 1024:
            video_bytes = open(input_src, "rb").read()
            part_kwargs = {"inline_data": types.Blob(data=video_bytes, mime_type=guess_mime(input_src))}
            if video_metadata:
                part_kwargs["video_metadata"] = video_metadata
            parts.append(types.Part(**part_kwargs))
        else:
            print(f"[gemini-video] 上传文件 (File API)...", file=sys.stderr)
            # Work around httpx ASCII header bug with non-ASCII filenames
            upload_path = input_src
            try:
                input_src.encode("ascii")
            except UnicodeEncodeError:
                import shutil, tempfile
                ext = os.path.splitext(input_src)[1] or ".mp4"
                tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
                tmp.close()
                shutil.copy2(input_src, tmp.name)
                upload_path = tmp.name
            uploaded = client.files.upload(file=upload_path)
            if upload_path != input_src:
                os.unlink(upload_path)
            uploaded = wait_for_processing(client, uploaded)
            print(f"[gemini-video] 文件已就绪: {uploaded.uri}", file=sys.stderr)

            part_kwargs = {"file_data": types.FileData(file_uri=uploaded.uri, mime_type=guess_mime(input_src))}
            if video_metadata:
                part_kwargs["video_metadata"] = video_metadata
            parts.append(types.Part(**part_kwargs))

    parts.append(types.Part(text=args.prompt))

    print(f"[gemini-video] 分析中: {args.prompt[:80]}...", file=sys.stderr)
    response = client.models.generate_content(
        model=args.model,
        contents=types.Content(parts=parts),
        config=types.GenerateContentConfig(**gen_config) if gen_config else None,
    )

    result = response.text
    if not result:
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if part.text:
                    result = (result or "") + part.text

    if not result:
        print("ERROR: No response from model", file=sys.stderr)
        sys.exit(1)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"[gemini-video] 结果已保存: {args.output}", file=sys.stderr)
    else:
        print(result)

    if tmp_file:
        os.unlink(tmp_file.name)


if __name__ == "__main__":
    main()
