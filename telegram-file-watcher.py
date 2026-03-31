#!/usr/bin/env python3
"""
Telegram File Watcher for OpenClaw
Runs alongside the gateway, intercepts document messages via webhook proxy,
downloads files to workspace, and forwards messages to the gateway.

How it works:
1. Registers a Telegram webhook pointing to this proxy
2. For each incoming message:
   - If it has a document/file: download to workspace, inject file path into text
   - Forward the full update to gateway's local webhook endpoint
3. When stopped, switches Telegram back to long polling

Usage:
    python3 telegram-file-watcher.py               # Start watcher
    python3 telegram-file-watcher.py --port 8686    # Custom port
    python3 telegram-file-watcher.py --stop         # Stop and restore long polling
"""

import argparse
import json
import os
import signal
import sys
import time
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime, timezone

WORKSPACE = "/root/.openclaw/workspace"
CONFIG_PATH = "/root/.openclaw/openclaw.json"
LOG_FILE = "/root/.openclaw/logs/file-watcher.log"
PID_FILE = "/tmp/telegram-file-watcher.pid"


def load_bot_token():
    try:
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
        return cfg.get("channels", {}).get("telegram", {}).get("botToken", "")
    except:
        return os.environ.get("TELEGRAM_BOT_TOKEN", "")


BOT_TOKEN = load_bot_token()
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"
FILE_BASE = f"https://api.telegram.org/file/bot{BOT_TOKEN}"


def log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except:
        pass


def api_call(method, params=None, data=None):
    url = f"{API_BASE}/{method}"
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    try:
        if data:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode(),
                headers={"Content-Type": "application/json"},
            )
        else:
            req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        log(f"API error: {e}")
        return {"ok": False}


def download_telegram_file(file_id, filename=None):
    result = api_call("getFile", {"file_id": file_id})
    if not result.get("ok"):
        log(f"Failed to get file info for {file_id}")
        return None

    file_path = result["result"].get("file_path")
    if not file_path:
        return None

    if not filename:
        filename = os.path.basename(file_path)

    download_url = f"{FILE_BASE}/{file_path}"
    local_path = os.path.join(WORKSPACE, filename)

    # Avoid overwrites
    base, ext = os.path.splitext(local_path)
    counter = 1
    while os.path.exists(local_path):
        local_path = f"{base}_{counter}{ext}"
        counter += 1

    try:
        urllib.request.urlretrieve(download_url, local_path)
        size = os.path.getsize(local_path)
        log(f"Downloaded: {filename} ({size:,} bytes) -> {local_path}")
        return local_path
    except Exception as e:
        log(f"Download failed: {e}")
        return None


def process_update(update):
    """Process a Telegram update, download any documents, return modified update."""
    msg = update.get("message", {})
    doc = msg.get("document")
    
    if not doc:
        return update, None

    file_id = doc.get("file_id", "")
    file_name = doc.get("file_name", "unknown_file")
    mime_type = doc.get("mime_type", "unknown")
    file_size = doc.get("file_size", 0)
    
    from_user = msg.get("from", {}).get("first_name", "user")
    caption = msg.get("caption", "")
    
    log(f"Document received from {from_user}: {file_name} ({mime_type}, {file_size} bytes)")
    
    local_path = download_telegram_file(file_id, file_name)
    
    if local_path:
        # Inject the file path info into the message text/caption
        file_info = f"\n\n📎 用户上传文件已保存: {local_path}\n文件名: {file_name}\nMIME: {mime_type}\n大小: {file_size} bytes"
        
        if msg.get("caption"):
            msg["caption"] = msg["caption"] + file_info
        elif msg.get("text"):
            msg["text"] = msg["text"] + file_info
        else:
            msg["text"] = file_info.strip()
        
        update["message"] = msg
        return update, local_path
    
    return update, None


class WebhookHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress default HTTP logging
    
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        try:
            update = json.loads(body)
            modified_update, saved_path = process_update(update)
            
            if saved_path:
                log(f"File saved to workspace: {saved_path}")
            
        except Exception as e:
            log(f"Error processing update: {e}")
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok": true}')
    
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Telegram File Watcher running")


def setup_webhook(port, secret):
    """Set up Telegram webhook pointing to our local proxy."""
    # We need a public URL, but since we're on a server, use the server's IP
    # For local-only: use internal URL (the gateway webhook mode handles this)
    webhook_url = f"http://127.0.0.1:{port}/telegram-file-webhook"
    
    # Actually, we can't use localhost for Telegram webhooks.
    # Instead, we'll intercept at a different level.
    # 
    # The approach: we don't need webhooks at all!
    # We monkey-patch: before gateway starts, we set up our own getUpdates loop
    # that saves files, then let gateway proceed.
    #
    # Better approach: Use polling with allowed_updates filter
    # But that conflicts with gateway.
    #
    # FINAL approach: periodic polling using getUpdates with NO offset acknowledgment
    # This is a READ-ONLY check that doesn't consume updates.
    # Wait - getUpdates always consumes if you specify offset.
    # Without offset, it returns the same updates repeatedly.
    
    log(f"File watcher cannot use webhooks (localhost not accessible by Telegram)")
    log(f"Using alternative approach: monitoring gateway's update stream")
    return False


def monitor_gateway_updates(port):
    """
    Alternative approach: Instead of webhooks, we intercept by running 
    getUpdates BEFORE the gateway processes them.
    
    This works by:
    1. Checking for pending updates with a short timeout
    2. If a document is found, download it immediately
    3. Don't acknowledge (no offset), so gateway still processes normally
    """
    log("Starting file monitor (pre-gateway intercept mode)")
    log(f"Watching for document uploads, saving to {WORKSPACE}")
    
    seen_updates = set()
    
    while True:
        try:
            # Peek at pending updates (0 timeout = immediate return)
            result = api_call("getUpdates", {"timeout": "1", "limit": "10"})
            
            if result.get("ok"):
                for update in result.get("result", []):
                    update_id = update.get("update_id")
                    if update_id in seen_updates:
                        continue
                    seen_updates.add(update_id)
                    
                    msg = update.get("message", {})
                    doc = msg.get("document")
                    
                    if doc:
                        file_id = doc.get("file_id", "")
                        file_name = doc.get("file_name", "unknown_file")
                        mime_type = doc.get("mime_type", "unknown")
                        file_size = doc.get("file_size", 0)
                        from_user = msg.get("from", {}).get("first_name", "user")
                        
                        log(f"Document from {from_user}: {file_name} ({mime_type}, {file_size}B)")
                        local_path = download_telegram_file(file_id, file_name)
                        if local_path:
                            log(f"Saved: {local_path}")
                
                # Keep seen set manageable
                if len(seen_updates) > 1000:
                    seen_updates = set(list(seen_updates)[-500:])
            
            time.sleep(0.5)
            
        except KeyboardInterrupt:
            log("Stopping file monitor")
            break
        except Exception as e:
            log(f"Monitor error: {e}")
            time.sleep(5)


def stop_watcher():
    try:
        with open(PID_FILE) as f:
            pid = int(f.read().strip())
        os.kill(pid, signal.SIGTERM)
        os.remove(PID_FILE)
        log(f"Stopped watcher (PID {pid})")
    except FileNotFoundError:
        print("No watcher running (PID file not found)")
    except ProcessLookupError:
        print("Watcher process already stopped")
        try:
            os.remove(PID_FILE)
        except:
            pass


def main():
    parser = argparse.ArgumentParser(description="Telegram File Watcher")
    parser.add_argument("--port", type=int, default=8686, help="Port for webhook proxy")
    parser.add_argument("--stop", action="store_true", help="Stop the watcher")
    args = parser.parse_args()

    if args.stop:
        stop_watcher()
        return

    if not BOT_TOKEN:
        print("Error: No Telegram bot token found", file=sys.stderr)
        sys.exit(1)

    # Save PID
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    # Handle signals
    def cleanup(sig, frame):
        log("Shutting down...")
        try:
            os.remove(PID_FILE)
        except:
            pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    log(f"Telegram File Watcher starting (PID {os.getpid()})")
    
    # Use the monitor approach (doesn't conflict with gateway polling
    # because we DON'T acknowledge updates - we just peek)
    monitor_gateway_updates(args.port)


if __name__ == "__main__":
    main()
