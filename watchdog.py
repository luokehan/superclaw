#!/usr/bin/env python3
"""
看门狗 v4 — 只检查 Gateway 进程是否存在
不调用 health 端点（agent 执行任务时 health 会超时导致误判）
"""
import subprocess
import time
import os
import json
import urllib.request
import urllib.parse
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
CHECK_INTERVAL = 120   # 每 2 分钟检查一次
FAIL_THRESHOLD = 5     # 连续 5 次进程不存在才重启（即 10 分钟）
OPENCLAW_CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")
CERT_FILE = os.path.expanduser("~/.openclaw/telegram-webhook.pem")

def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=10
        )
    except Exception:
        pass

def gateway_alive():
    """pgrep 检查进程，不走网络"""
    try:
        r = subprocess.run(["pgrep", "-f", "openclaw-gateway"],
                           capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False

def re_register_webhook():
    """Gateway 重启后重新注册 Telegram webhook（带证书+密钥）"""
    try:
        with open(OPENCLAW_CONFIG) as f:
            cfg = json.load(f)
        tg = cfg["channels"]["telegram"]
        bot_token = tg["botToken"]
        secret = tg.get("webhookSecret", "")
        webhook_url = tg.get("webhookUrl", "https://YOUR_SERVER_IP:8443/webhook")

        import http.client
        import mimetypes
        boundary = "----WebhookBoundary"
        body_parts = []
        body_parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"url\"\r\n\r\n{webhook_url}")
        if secret:
            body_parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"secret_token\"\r\n\r\n{secret}")
        with open(CERT_FILE, "rb") as cf:
            cert_data = cf.read()
        body_parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"certificate\"; filename=\"cert.pem\"\r\n"
            f"Content-Type: application/x-pem-file\r\n\r\n"
        )
        body_bytes = "\r\n".join(body_parts).encode() + b"\r\n" + cert_data + f"\r\n--{boundary}--\r\n".encode()

        req = urllib.request.Request(
            f"https://api.telegram.org/bot{bot_token}/setWebhook",
            data=body_bytes,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                print("[Watchdog] Webhook re-registered successfully")
                return True
            else:
                print(f"[Watchdog] Webhook registration failed: {result}")
                return False
    except Exception as e:
        print(f"[Watchdog] Webhook re-registration error: {e}")
        return False

def restart_gateway():
    subprocess.run(["pkill", "-f", "openclaw-gateway"], capture_output=True)
    time.sleep(5)
    env = os.environ.copy()
    env["DISPLAY"] = ":10"
    subprocess.Popen(
        ["openclaw", "gateway", "--force", "--auth", "none", "--bind", "loopback"],
        stdout=open("/tmp/gw-watchdog.log", "w"),
        stderr=subprocess.STDOUT, env=env
    )
    time.sleep(20)
    alive = gateway_alive()
    if alive:
        time.sleep(5)
        re_register_webhook()
    return alive

def main():
    print("[Watchdog v4] process-check mode, interval=120s, threshold=5")
    fails = 0
    while True:
        if gateway_alive():
            fails = 0
        else:
            fails += 1
            print(f"[Watchdog] process missing ({fails}/{FAIL_THRESHOLD})")
            if fails >= FAIL_THRESHOLD:
                send_telegram("⚠️ 看门狗：Gateway 进程消失超过 10 分钟，正在重启...")
                ok = restart_gateway()
                send_telegram("✅ Gateway 重启成功" if ok else "❌ Gateway 重启失败，需要人工检查")
                fails = 0
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
