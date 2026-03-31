#!/usr/bin/env python3
"""Gemini 图片理解工具 — 单张/多张图片分析

Usage:
  python3 image-understand.py "描述这张图片" --input photo.jpg
  python3 image-understand.py "提取图中文字" --input img1.png img2.png img3.png
  python3 image-understand.py "这个产品怎么样" --input *.jpg --output analysis.md
"""
import argparse
import glob
import os
import sys


def load_env():
    env_path = "/root/openclaw-fusion/data/.env"
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


def main():
    parser = argparse.ArgumentParser(description="Gemini Image Understanding")
    parser.add_argument("prompt", help="提问内容")
    parser.add_argument("--input", nargs="+", required=True, help="图片路径（支持多张、通配符）")
    parser.add_argument("--output", help="保存结果到文件")
    parser.add_argument("--model", default="gemini-3.1-pro-preview", help="模型名称")
    args = parser.parse_args()

    load_env()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    # Expand globs
    image_paths = []
    for p in args.input:
        expanded = glob.glob(p)
        if expanded:
            image_paths.extend(expanded)
        elif os.path.exists(p):
            image_paths.append(p)
        else:
            print(f"WARNING: {p} not found", file=sys.stderr)

    if not image_paths:
        print("ERROR: No valid image files", file=sys.stderr)
        sys.exit(1)

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    parts = []

    for img_path in image_paths[:20]:
        try:
            data = open(img_path, "rb").read()
            ext = os.path.splitext(img_path)[1].lower()
            mime = {".png": "image/png", ".webp": "image/webp", ".gif": "image/gif"}.get(ext, "image/jpeg")
            parts.append(types.Part(inline_data=types.Blob(data=data, mime_type=mime)))
            print(f"[gemini-image] 加载: {img_path} ({len(data)//1024}KB)", file=sys.stderr)
        except Exception as e:
            print(f"[gemini-image] 跳过 {img_path}: {e}", file=sys.stderr)

    parts.append(types.Part(text=args.prompt))

    print(f"[gemini-image] 分析 {len(parts)-1} 张图片...", file=sys.stderr)
    response = client.models.generate_content(
        model=args.model,
        contents=types.Content(parts=parts),
    )

    result = response.text or ""
    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"[gemini-image] 已保存: {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
