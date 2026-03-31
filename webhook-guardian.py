#!/usr/bin/env python3
"""
Webhook Guardian — auto-recovers Telegram webhook after gateway restarts.

Monitors:
1. Gateway process alive
2. Telegram webhook has valid certificate
3. No recent webhook delivery errors

On failure: re-registers webhook with self-signed cert + secret.
"""
import json
import os
import subprocess
import time
import urllib.request
import urllib.error
import datetime

CONFIG_PATH = "/root/.openclaw/openclaw.json"
CERT_PATH = "/root/.openclaw/telegram-webhook.pem"
GATEWAY_HEALTH = "http://127.0.0.1:18789/health"
CHECK_INTERVAL = 30  # seconds
STARTUP_DELAY = 10   # wait for gateway to be ready after restart


def load_config():
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    tg = cfg["channels"]["telegram"]
    return {
        "bot_token": tg["botToken"],
        "webhook_url": tg["webhookUrl"],
        "webhook_secret": tg["webhookSecret"],
    }


def gateway_alive() -> bool:
    try:
        req = urllib.request.Request(GATEWAY_HEALTH, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return data.get("ok", False)
    except Exception:
        return False


def get_webhook_info(bot_token: str) -> dict:
    url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read()).get("result", {})
    except Exception as e:
        return {"error": str(e)}


def register_webhook(bot_token: str, webhook_url: str, secret: str) -> bool:
    # Delete first
    try:
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{bot_token}/deleteWebhook", timeout=10
        )
    except Exception:
        pass

    # Re-register with cert
    result = subprocess.run(
        [
            "curl", "-s", "-X", "POST",
            f"https://api.telegram.org/bot{bot_token}/setWebhook",
            "-F", f"url={webhook_url}",
            "-F", f"certificate=@{CERT_PATH}",
            "-F", f"secret_token={secret}",
            "-F", 'allowed_updates=["message","callback_query","edited_message"]',
        ],
        capture_output=True, text=True, timeout=15,
    )
    try:
        resp = json.loads(result.stdout)
        return resp.get("ok", False)
    except Exception:
        return False


def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def send_telegram_alert(bot_token: str, message: str):
    """Best-effort alert via Telegram — extract chat_id from session-watcher."""
    try:
        with open("/root/openclaw-fusion/session-watcher.py") as f:
            content = f.read()
        import re
        match = re.search(r'CHAT_ID\s*=\s*["\']([^"\']+)', content)
        if not match:
            return
        chat_id = match.group(1)
        data = json.dumps({"chat_id": chat_id, "text": message}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass


def main():
    log("Webhook Guardian started")
    cfg = load_config()
    last_recovery = 0
    consecutive_failures = 0

    while True:
        try:
            # 1. Check gateway
            if not gateway_alive():
                log("Gateway not responding, waiting...")
                time.sleep(CHECK_INTERVAL)
                continue

            # 2. Check webhook
            info = get_webhook_info(cfg["bot_token"])
            if "error" in info:
                log(f"Cannot reach Telegram API: {info['error']}")
                time.sleep(CHECK_INTERVAL)
                continue

            has_cert = info.get("has_custom_certificate", False)
            last_error = info.get("last_error_message", "")
            webhook_url = info.get("url", "")

            needs_recovery = False
            reason = ""

            if not webhook_url:
                needs_recovery = True
                reason = "webhook URL is empty"
            elif not has_cert:
                needs_recovery = True
                reason = "custom certificate missing"
            elif "SSL" in last_error or "certificate" in last_error.lower():
                needs_recovery = True
                reason = f"SSL error: {last_error}"
            elif webhook_url != cfg["webhook_url"]:
                needs_recovery = True
                reason = f"URL mismatch: {webhook_url} != {cfg['webhook_url']}"

            if needs_recovery:
                now = time.time()
                if now - last_recovery < 60:
                    log(f"Recovery needed ({reason}) but cooldown active, skipping")
                    time.sleep(CHECK_INTERVAL)
                    continue

                log(f"Recovery needed: {reason}")
                time.sleep(STARTUP_DELAY)  # wait for gateway TLS to be ready

                ok = register_webhook(
                    cfg["bot_token"], cfg["webhook_url"], cfg["webhook_secret"]
                )
                last_recovery = time.time()

                if ok:
                    log("Webhook recovered successfully")
                    send_telegram_alert(
                        cfg["bot_token"],
                        f"🔧 Webhook 自动恢复成功\n原因: {reason}"
                    )
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    log(f"Recovery failed (attempt {consecutive_failures})")
                    if consecutive_failures >= 3:
                        send_telegram_alert(
                            cfg["bot_token"],
                            f"⚠️ Webhook 恢复连续失败 {consecutive_failures} 次\n原因: {reason}"
                        )
            else:
                consecutive_failures = 0

        except Exception as e:
            log(f"Error: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
