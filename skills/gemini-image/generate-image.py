#!/usr/bin/env python3
"""Gemini 图片生成工具 — 文生图 / 图编辑 / 自动放大到 2K

Usage:
  python3 generate-image.py "提示词" --output path/to/image.png
  python3 generate-image.py "提示词" --output image.png --size 2k
  python3 generate-image.py "提示词" --output image.png --size 1080x1920
  python3 generate-image.py "把背景改成蓝色" --input source.png --output edited.png
"""
import argparse
import os
import sys

SIZE_PRESETS = {
    "2k": 2048,
    "1080p": 1920,
    "4k": 3840,
    "1k": 1024,
}


def upscale_image(path, target_size):
    """放大图片到目标尺寸（保持长边=target_size，等比缩放）"""
    from PIL import Image

    img = Image.open(path)
    w, h = img.size

    if isinstance(target_size, tuple):
        target_w, target_h = target_size
    else:
        if w >= h:
            target_w = target_size
            target_h = int(h * target_size / w)
        else:
            target_h = target_size
            target_w = int(w * target_size / h)

    if target_w <= w and target_h <= h:
        print(f"[gemini-image] 原图 {w}x{h} 已满足目标，跳过放大", file=sys.stderr)
        return

    img_resized = img.resize((target_w, target_h), Image.LANCZOS)
    img_resized.save(path)
    print(f"[gemini-image] 已放大: {w}x{h} → {target_w}x{target_h}", file=sys.stderr)


def parse_size(size_str):
    """解析尺寸参数：'2k' / '1080x1920' / '2048'"""
    if not size_str:
        return None
    size_str = size_str.lower().strip()
    if size_str in SIZE_PRESETS:
        return SIZE_PRESETS[size_str]
    if "x" in size_str:
        parts = size_str.split("x")
        return (int(parts[0]), int(parts[1]))
    return int(size_str)


def main():
    parser = argparse.ArgumentParser(description="Gemini Image Generator")
    parser.add_argument("prompt", help="图片生成提示词")
    parser.add_argument("--output", required=True, help="输出图片路径 (.png)")
    parser.add_argument("--input", help="输入图片路径（图片编辑模式）")
    parser.add_argument("--size", default="2k", help="输出尺寸: 2k(默认), 4k, 1080p, 1k, 或 宽x高 如 1080x1920")
    parser.add_argument("--model", default="gemini-3.1-flash-image-preview", help="模型名称")
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    contents = []
    if args.input:
        if not os.path.exists(args.input):
            print(f"ERROR: Input file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        img_data = open(args.input, "rb").read()
        ext = os.path.splitext(args.input)[1].lower()
        mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(ext, "image/png")
        contents.append(types.Part.from_bytes(data=img_data, mime_type=mime))
        print(f"[gemini-image] 编辑模式: {args.input} ({len(img_data)} bytes)", file=sys.stderr)

    contents.append(args.prompt)

    print(f"[gemini-image] 生成中: {args.prompt[:60]}...", file=sys.stderr)
    response = client.models.generate_content(
        model=args.model,
        contents=contents,
        config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"])
    )

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    generated = False
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            with open(args.output, "wb") as f:
                f.write(part.inline_data.data)
            print(f"[gemini-image] 原图已保存: {args.output} ({len(part.inline_data.data)} bytes)", file=sys.stderr)
            generated = True
        elif part.text:
            print(part.text)

    if not generated:
        print("ERROR: No image generated", file=sys.stderr)
        sys.exit(1)

    target = parse_size(args.size)
    if target:
        upscale_image(args.output, target)

    from PIL import Image
    img = Image.open(args.output)
    print(f"[gemini-image] 最终尺寸: {img.size[0]}x{img.size[1]}", file=sys.stderr)


if __name__ == "__main__":
    main()
