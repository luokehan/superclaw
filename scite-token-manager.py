#!/usr/bin/env python3
"""
Scite OAuth Token Manager — Auto-refresh, never expires.

Uses OAuth refresh_token to automatically renew access_token before expiry.
No manual intervention needed after initial OAuth authorization.

Usage:
  python3 scite-token-manager.py check       # Check token status
  python3 scite-token-manager.py refresh      # Force refresh now
  python3 scite-token-manager.py update <JWT> # Manual token update (fallback)
  python3 scite-token-manager.py watch        # Run as daemon, auto-refresh
"""
import sys
import os
import json
import base64
import time
import datetime
import urllib.request
import urllib.parse
import urllib.error

MCPORTER_CONFIG = os.path.expanduser("~/.mcporter/mcporter.json")
OAUTH_TOKENS_FILE = "/root/openclaw-fusion/data/.scite_oauth_tokens"
OAUTH_STATE_FILE = "/root/openclaw-fusion/data/.scite_oauth_state"
ENV_FILE = "/root/openclaw-fusion/data/.env"
TOKEN_ENDPOINT = "https://api.scite.ai/mcp/oauth/token"

REFRESH_BEFORE_SECONDS = 3600  # refresh 1 hour before expiry
CHECK_INTERVAL = 600  # check every 10 min


def decode_jwt_payload(token: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT")
    payload = parts[1]
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


def get_current_token() -> str | None:
    try:
        with open(MCPORTER_CONFIG) as f:
            cfg = json.load(f)
        auth = cfg.get("mcpServers", {}).get("scite", {}).get("headers", {}).get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:]
    except Exception:
        pass
    return None


def get_oauth_tokens() -> dict | None:
    try:
        with open(OAUTH_TOKENS_FILE) as f:
            return json.load(f)
    except Exception:
        return None


def get_client_id() -> str:
    try:
        with open(OAUTH_STATE_FILE) as f:
            return json.load(f).get("client_id", "")
    except Exception:
        return "oauth_PXdyQYbNddMc4Rpbc4vi5A"


def save_oauth_tokens(tokens: dict):
    with open(OAUTH_TOKENS_FILE, "w") as f:
        json.dump(tokens, f, indent=2)
    os.chmod(OAUTH_TOKENS_FILE, 0o600)


def update_mcporter(access_token: str):
    try:
        with open(MCPORTER_CONFIG) as f:
            cfg = json.load(f)
    except Exception:
        cfg = {"mcpServers": {"scite": {"baseUrl": "https://api.scite.ai/mcp"}}, "imports": []}

    cfg.setdefault("mcpServers", {}).setdefault("scite", {})["headers"] = {
        "Authorization": f"Bearer {access_token}"
    }
    with open(MCPORTER_CONFIG, "w") as f:
        json.dump(cfg, f, indent=2)
    os.chmod(MCPORTER_CONFIG, 0o600)


def refresh_token() -> dict:
    """Use refresh_token to get a new access_token."""
    tokens = get_oauth_tokens()
    if not tokens or "refresh_token" not in tokens:
        return {"error": "No refresh_token available"}

    client_id = get_client_id()
    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": tokens["refresh_token"],
        "client_id": client_id,
    }).encode()

    req = urllib.request.Request(
        TOKEN_ENDPOINT,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            new_tokens = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return {"error": f"Refresh failed ({e.code}): {body}"}
    except Exception as e:
        return {"error": f"Refresh failed: {e}"}

    if "access_token" not in new_tokens:
        return {"error": f"No access_token in response: {new_tokens}"}

    # Preserve refresh_token if new one not provided
    if "refresh_token" not in new_tokens and "refresh_token" in tokens:
        new_tokens["refresh_token"] = tokens["refresh_token"]

    # Save and update
    new_tokens["refreshed_at"] = datetime.datetime.now().isoformat()
    save_oauth_tokens(new_tokens)
    update_mcporter(new_tokens["access_token"])

    expires_in = new_tokens.get("expires_in", "unknown")
    return {
        "success": True,
        "expires_in": expires_in,
        "has_refresh_token": "refresh_token" in new_tokens,
        "refreshed_at": new_tokens["refreshed_at"],
    }


def check_token() -> dict:
    token = get_current_token()
    if not token:
        return {"status": "missing", "message": "No Scite token configured"}

    try:
        payload = decode_jwt_payload(token)
    except Exception as e:
        return {"status": "invalid", "message": f"Cannot decode: {e}"}

    exp = datetime.datetime.fromtimestamp(payload["exp"])
    now = datetime.datetime.now()
    remaining = exp - now

    tokens = get_oauth_tokens()
    has_refresh = tokens is not None and "refresh_token" in tokens

    if remaining.total_seconds() <= 0:
        return {
            "status": "expired",
            "message": f"Expired at {exp.isoformat()}",
            "has_refresh_token": has_refresh,
            "auto_refresh": has_refresh,
        }

    return {
        "status": "valid",
        "plan": payload.get("plan", "unknown"),
        "org": payload.get("organization_name", ""),
        "expires": exp.isoformat(),
        "remaining": str(remaining).split(".")[0],
        "remaining_seconds": remaining.total_seconds(),
        "has_refresh_token": has_refresh,
        "auto_refresh": has_refresh,
    }


def update_token_manual(new_token: str) -> dict:
    try:
        payload = decode_jwt_payload(new_token)
    except Exception as e:
        return {"error": f"Invalid JWT: {e}"}

    exp = datetime.datetime.fromtimestamp(payload["exp"])
    if exp < datetime.datetime.now():
        return {"error": "Token is already expired"}

    update_mcporter(new_token)

    remaining = exp - datetime.datetime.now()
    return {
        "success": True,
        "plan": payload.get("plan"),
        "org": payload.get("organization_name"),
        "expires": exp.isoformat(),
        "remaining": str(remaining).split(".")[0],
    }


def send_telegram(message: str):
    try:
        sw_path = "/root/openclaw-fusion/session-watcher.py"
        with open(sw_path) as f:
            content = f.read()
        import re
        bot_match = re.search(r'BOT_TOKEN\s*=\s*["\']([^"\']+)', content)
        chat_match = re.search(r'CHAT_ID\s*=\s*["\']([^"\']+)', content)
        if not (bot_match and chat_match):
            return
        bot_token = bot_match.group(1)
        chat_id = chat_match.group(1)
    except Exception:
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = json.dumps({"chat_id": chat_id, "text": message, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass


def watch():
    print(f"[scite-token-manager] Auto-refresh daemon started (check every {CHECK_INTERVAL}s)")
    consecutive_failures = 0

    while True:
        info = check_token()

        if info["status"] == "valid":
            remaining = info["remaining_seconds"]
            if remaining <= REFRESH_BEFORE_SECONDS and info.get("has_refresh_token"):
                print(f"[refresh] Token expires in {info['remaining']}, refreshing...")
                result = refresh_token()
                if "success" in result:
                    print(f"[refresh] Success! New token expires in {result['expires_in']}s")
                    send_telegram(
                        f"🔄 <b>Scite Token 自动续期成功</b>\n"
                        f"新 token 有效期: {result['expires_in']}s"
                    )
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    print(f"[refresh] Failed: {result.get('error')}")
                    if consecutive_failures >= 3:
                        send_telegram(
                            f"⚠️ <b>Scite Token 自动续期失败</b>\n"
                            f"已连续失败 {consecutive_failures} 次\n"
                            f"错误: {result.get('error', 'unknown')}\n\n"
                            f"可能需要重新授权。"
                        )

        elif info["status"] == "expired":
            if info.get("has_refresh_token"):
                print("[refresh] Token expired, attempting refresh...")
                result = refresh_token()
                if "success" in result:
                    print(f"[refresh] Recovered! New token expires in {result['expires_in']}s")
                    send_telegram(
                        f"✅ <b>Scite Token 过期后自动恢复</b>\n"
                        f"新 token 有效期: {result['expires_in']}s"
                    )
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    print(f"[refresh] Failed: {result.get('error')}")
            else:
                print("[watch] Token expired, no refresh_token available")

        elif info["status"] == "missing":
            pass  # No token configured

        time.sleep(CHECK_INTERVAL)


def main():
    if len(sys.argv) < 2:
        print("Usage: scite-token-manager.py check|refresh|update <token>|watch")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "check":
        info = check_token()
        print(json.dumps(info, indent=2, ensure_ascii=False))

    elif cmd == "refresh":
        result = refresh_token()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "update":
        if len(sys.argv) < 3:
            print("Usage: scite-token-manager.py update <JWT>")
            sys.exit(1)
        result = update_token_manual(sys.argv[2])
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "watch":
        watch()

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
