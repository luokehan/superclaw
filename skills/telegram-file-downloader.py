#!/usr/bin/env python3
"""
Telegram File Downloader for SuperClaw
Downloads the most recent file(s) sent by users via Telegram Bot API.

Usage:
    python3 telegram-file-downloader.py                    # Download latest file
    python3 telegram-file-downloader.py --list             # List recent files (no download)
    python3 telegram-file-downloader.py --count 3          # Download last 3 files
    python3 telegram-file-downloader.py --output /path/    # Custom output dir
    python3 telegram-file-downloader.py --file-id <id>     # Download specific file by file_id
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
if not BOT_TOKEN:
    token_paths = [
        "/root/.openclaw/openclaw.json",
    ]
    for p in token_paths:
        try:
            with open(p) as f:
                cfg = json.load(f)
            t = cfg.get("channels", {}).get("telegram", {}).get("botToken", "")
            if t:
                BOT_TOKEN = t
                break
        except:
            pass

if not BOT_TOKEN:
    print("Error: No Telegram bot token found", file=sys.stderr)
    sys.exit(1)

API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"
FILE_BASE = f"https://api.telegram.org/file/bot{BOT_TOKEN}"
DEFAULT_OUTPUT = "/root/.openclaw/workspace"


def api_call(method, params=None):
    url = f"{API_BASE}/{method}"
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"API error {e.code}: {body}", file=sys.stderr)
        return {"ok": False, "description": body}


def download_file(file_id, output_dir, filename=None):
    result = api_call("getFile", {"file_id": file_id})
    if not result.get("ok"):
        print(f"Failed to get file info: {result.get('description', 'unknown')}", file=sys.stderr)
        return None

    file_path = result["result"].get("file_path")
    if not file_path:
        print("No file_path returned", file=sys.stderr)
        return None

    download_url = f"{FILE_BASE}/{file_path}"
    if not filename:
        filename = os.path.basename(file_path)

    os.makedirs(output_dir, exist_ok=True)
    local_path = os.path.join(output_dir, filename)

    try:
        urllib.request.urlretrieve(download_url, local_path)
        size = os.path.getsize(local_path)
        print(f"Downloaded: {local_path} ({size:,} bytes)")
        return local_path
    except Exception as e:
        print(f"Download failed: {e}", file=sys.stderr)
        return None


def get_recent_files(count=10):
    result = api_call("getUpdates", {"offset": "-100", "limit": "100"})
    if not result.get("ok"):
        print(f"Failed to get updates: {result.get('description', '')}", file=sys.stderr)
        return []

    files = []
    for update in result.get("result", []):
        msg = update.get("message", {})
        doc = msg.get("document")
        photo = msg.get("photo")
        audio = msg.get("audio")
        video = msg.get("video")
        voice = msg.get("voice")

        if doc:
            files.append({
                "type": "document",
                "file_id": doc["file_id"],
                "file_name": doc.get("file_name", "unknown"),
                "mime_type": doc.get("mime_type", "unknown"),
                "file_size": doc.get("file_size", 0),
                "date": msg.get("date", 0),
                "from": msg.get("from", {}).get("first_name", "unknown"),
                "caption": msg.get("caption", ""),
                "update_id": update["update_id"],
            })
        elif photo:
            largest = photo[-1]
            files.append({
                "type": "photo",
                "file_id": largest["file_id"],
                "file_name": f"photo_{msg.get('date', 0)}.jpg",
                "mime_type": "image/jpeg",
                "file_size": largest.get("file_size", 0),
                "date": msg.get("date", 0),
                "from": msg.get("from", {}).get("first_name", "unknown"),
                "caption": msg.get("caption", ""),
                "update_id": update["update_id"],
            })
        elif audio:
            files.append({
                "type": "audio",
                "file_id": audio["file_id"],
                "file_name": audio.get("file_name", f"audio_{msg.get('date', 0)}.mp3"),
                "mime_type": audio.get("mime_type", "audio/mpeg"),
                "file_size": audio.get("file_size", 0),
                "date": msg.get("date", 0),
                "from": msg.get("from", {}).get("first_name", "unknown"),
                "caption": msg.get("caption", ""),
                "update_id": update["update_id"],
            })
        elif video:
            files.append({
                "type": "video",
                "file_id": video["file_id"],
                "file_name": video.get("file_name", f"video_{msg.get('date', 0)}.mp4"),
                "mime_type": video.get("mime_type", "video/mp4"),
                "file_size": video.get("file_size", 0),
                "date": msg.get("date", 0),
                "from": msg.get("from", {}).get("first_name", "unknown"),
                "caption": msg.get("caption", ""),
                "update_id": update["update_id"],
            })
        elif voice:
            files.append({
                "type": "voice",
                "file_id": voice["file_id"],
                "file_name": f"voice_{msg.get('date', 0)}.ogg",
                "mime_type": voice.get("mime_type", "audio/ogg"),
                "file_size": voice.get("file_size", 0),
                "date": msg.get("date", 0),
                "from": msg.get("from", {}).get("first_name", "unknown"),
                "caption": msg.get("caption", ""),
                "update_id": update["update_id"],
            })

    files.sort(key=lambda x: x["date"], reverse=True)
    return files[:count]


def main():
    parser = argparse.ArgumentParser(description="Download files from Telegram")
    parser.add_argument("--list", action="store_true", help="List recent files without downloading")
    parser.add_argument("--count", type=int, default=1, help="Number of files to download (default: 1)")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output directory")
    parser.add_argument("--file-id", help="Download specific file by file_id")
    parser.add_argument("--filename", help="Override output filename")
    args = parser.parse_args()

    if args.file_id:
        result = download_file(args.file_id, args.output, args.filename)
        if result:
            print(f"\nFile saved to: {result}")
        else:
            sys.exit(1)
        return

    files = get_recent_files(max(args.count, 10))

    if not files:
        print("No recent files found in Telegram updates.")
        print("Note: Updates are consumed after being read by the gateway.")
        print("The file may have already been processed. Ask the user to re-send.")
        sys.exit(1)

    if args.list:
        print(f"Recent files ({len(files)}):\n")
        for i, f in enumerate(files):
            dt = datetime.fromtimestamp(f["date"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            size_kb = f["file_size"] / 1024
            print(f"  [{i+1}] {f['file_name']} ({f['type']}, {size_kb:.1f}KB)")
            print(f"      from: {f['from']}, date: {dt}")
            print(f"      mime: {f['mime_type']}")
            print(f"      file_id: {f['file_id']}")
            if f["caption"]:
                print(f"      caption: {f['caption']}")
            print()
        return

    downloaded = 0
    for f in files[:args.count]:
        dt = datetime.fromtimestamp(f["date"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        print(f"\nDownloading: {f['file_name']} ({f['type']}, from {f['from']}, {dt})")
        result = download_file(f["file_id"], args.output, f["file_name"])
        if result:
            downloaded += 1

    print(f"\nDownloaded {downloaded}/{args.count} file(s) to {args.output}")


if __name__ == "__main__":
    main()
