#!/usr/bin/env python3
"""OpenMOSS Telegram 通知工具 — Agent 调用发送消息到 Telegram

Usage:
  python3 skills/notify.py "消息内容"
  python3 skills/notify.py "消息内容" --parse-mode Markdown
"""
import argparse
import sys
import os
import yaml
from urllib.request import Request, urlopen
from urllib.parse import urlencode

def load_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def send_telegram(bot_token, chat_id, text, parse_mode=None):
    params = {"chat_id": chat_id, "text": text}
    if parse_mode:
        params["parse_mode"] = parse_mode
    data = urlencode(params).encode()
    req = Request(f"https://api.telegram.org/bot{bot_token}/sendMessage", data=data)
    try:
        resp = urlopen(req, timeout=10)
        return resp.status == 200
    except Exception as e:
        print(f"发送失败: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Send notification to Telegram")
    parser.add_argument("message", help="消息内容")
    parser.add_argument("--parse-mode", default=None, choices=["Markdown", "HTML"])
    args = parser.parse_args()

    config = load_config()
    notif = config.get("notification", {})

    if not notif.get("enabled"):
        print("通知未启用")
        return

    channels = notif.get("channels", [])
    sent = 0
    for ch in channels:
        if ch.get("type") == "telegram":
            ok = send_telegram(ch["bot_token"], ch["chat_id"], args.message, args.parse_mode)
            if ok:
                sent += 1
                print(f"已发送到 Telegram (chat_id: {ch['chat_id']})")

    if sent == 0:
        print("未找到可用的 Telegram 渠道")

if __name__ == "__main__":
    main()
