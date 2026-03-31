#!/usr/bin/env python3
"""
Telegram File Proxy for OpenClaw (HTTPS)

Sits between Telegram and OpenClaw gateway as a webhook proxy.
Downloads document files to workspace before forwarding to gateway.

Architecture:
  Telegram -> https://SERVER:8686/webhook -> this proxy (HTTPS) -> http://127.0.0.1:8787/telegram-webhook -> gateway
"""

import json
import os
import ssl
import sys
import signal
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone

WORKSPACE = "/root/.openclaw/workspace"
CONFIG_PATH = "/root/.openclaw/openclaw.json"
LOG_FILE = "/root/.openclaw/logs/file-proxy.log"
PID_FILE = "/tmp/telegram-file-proxy.pid"
CERT_FILE = "/root/.openclaw/telegram-webhook.pem"
KEY_FILE = "/root/.openclaw/telegram-webhook.key"
GATEWAY_WEBHOOK = "http://127.0.0.1:8787/telegram-webhook"


def load_config():
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    tg = cfg.get("channels", {}).get("telegram", {})
    return {
        "bot_token": tg.get("botToken", ""),
        "webhook_secret": tg.get("webhookSecret", ""),
    }


CFG = load_config()
API_BASE = f"https://api.telegram.org/bot{CFG['bot_token']}"
FILE_BASE = f"https://api.telegram.org/file/bot{CFG['bot_token']}"


def log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except:
        pass


def download_telegram_file(file_id, filename=None):
    try:
        url = f"{API_BASE}/getFile?file_id={file_id}"
        with urllib.request.urlopen(url, timeout=30) as resp:
            result = json.loads(resp.read())
        if not result.get("ok"):
            return None
        file_path = result["result"].get("file_path")
        if not file_path:
            return None
        if not filename:
            filename = os.path.basename(file_path)
        download_url = f"{FILE_BASE}/{file_path}"
        local_path = os.path.join(WORKSPACE, filename)
        base, ext = os.path.splitext(local_path)
        counter = 1
        while os.path.exists(local_path):
            local_path = f"{base}_{counter}{ext}"
            counter += 1
        urllib.request.urlretrieve(download_url, local_path)
        size = os.path.getsize(local_path)
        log(f"Downloaded: {filename} ({size:,} bytes) -> {local_path}")
        return local_path
    except Exception as e:
        log(f"Download error: {e}")
        return None


def forward_to_gateway(body, headers):
    try:
        req = urllib.request.Request(
            GATEWAY_WEBHOOK,
            data=body,
            headers={"Content-Type": "application/json"},
        )
        secret = headers.get("X-Telegram-Bot-Api-Secret-Token")
        if secret:
            req.add_header("X-Telegram-Bot-Api-Secret-Token", secret)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status
    except Exception as e:
        log(f"Forward error: {e}")
        return 500


class ProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            update = json.loads(body)
            msg = update.get("message", {})
            doc = msg.get("document")

            if doc:
                file_id = doc.get("file_id", "")
                file_name = doc.get("file_name", "uploaded_file")
                mime_type = doc.get("mime_type", "unknown")
                file_size = doc.get("file_size", 0)
                from_user = msg.get("from", {}).get("first_name", "user")

                log(f"Document from {from_user}: {file_name} ({mime_type}, {file_size}B)")
                local_path = download_telegram_file(file_id, file_name)

                if local_path:
                    file_note = f"\n\n📎 文件已保存到: {local_path}"
                    if msg.get("caption"):
                        msg["caption"] = msg["caption"] + file_note
                    else:
                        msg["caption"] = f"用户上传了文件: {file_name}{file_note}"
                    update["message"] = msg
                    body = json.dumps(update).encode()

        except Exception as e:
            log(f"Processing error: {e}")

        forward_to_gateway(body, dict(self.headers))

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok": true}')

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Telegram File Proxy OK")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8686)
    args = parser.parse_args()

    if not CFG["bot_token"]:
        print("Error: No bot token", file=sys.stderr)
        sys.exit(1)

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    def cleanup(sig, frame):
        log("Shutting down proxy...")
        try:
            os.remove(PID_FILE)
        except:
            pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    server = HTTPServer(("0.0.0.0", args.port), ProxyHandler)

    # Wrap with SSL
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(CERT_FILE, KEY_FILE)
    server.socket = ctx.wrap_socket(server.socket, server_side=True)

    log(f"Telegram File Proxy (HTTPS) started on port {args.port}")
    log(f"Forwarding to: {GATEWAY_WEBHOOK}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        cleanup(None, None)


if __name__ == "__main__":
    main()
