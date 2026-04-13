#!/usr/bin/env python3
"""
Claude usage - sem dependências externas
Usa sqlite3 (stdlib) para ler cookies do navegador + curl para API
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import time
from pathlib import Path


CLAUDE_DOMAIN = "claude.ai"
CACHE_FILE = Path.home() / ".cache" / "waybar-ai-usage" / "claude.json"
CACHE_TTL = 120


def get_chromium_key() -> bytes | None:
    """Get Chrome/Brave encryption key"""
    try:
        import base64
        import sys

        if sys.platform == "linux":
            key_paths = [
                Path.home() / ".config" / "chromium" / "Local State",
                Path.home() / ".config" / "chrome" / "Local State",
                Path.home()
                / ".config"
                / "BraveSoftware"
                / "Brave-Browser"
                / "Local State",
            ]
        else:
            return None

        for key_path in key_paths:
            if not key_path.exists():
                continue
            try:
                content = key_path.read_text()
                data = json.loads(content)
                key_b64 = data.get("os_crypt", {}).get("encrypted_key")
                if key_b64:
                    key = base64.b64decode(key_b64)
                    return key[5:]
            except Exception:
                continue
    except Exception:
        pass
    return None


def decrypt_chromium_cookie(encrypted_value: bytes, key: bytes) -> str:
    """Decrypt Chromium cookie value"""
    try:
        from cryptography.fernet import Fernet

        f = Fernet(key)
        return f.decrypt(encrypted_value).decode()
    except Exception:
        return ""


def get_chromium_cookies(domain: str) -> dict:
    """Lê cookies do Chromium/Brave usando sqlite3 (stdlib)"""
    cookie_paths = [
        Path.home() / ".config" / "chromium" / "Default" / "Cookies",
        Path.home() / ".config" / "chrome" / "Default" / "Cookies",
        Path.home() / ".config" / "google-chrome" / "Default" / "Cookies",
        Path.home()
        / ".config"
        / "BraveSoftware"
        / "Brave-Browser"
        / "Default"
        / "Cookies",
    ]

    key = get_chromium_key()

    cookies = {}
    for cookie_path in cookie_paths:
        if not cookie_path.exists():
            continue
        try:
            conn = sqlite3.connect(cookie_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT name, value, encrypted_value FROM cookies WHERE host_key LIKE ? AND name != ''",
                (f"%{domain}",),
            )
            for row in cursor:
                name = row["name"]
                value = row["value"]
                if not value and row["encrypted_value"] and key:
                    value = decrypt_chromium_cookie(row["encrypted_value"], key)
                if value:
                    cookies[name] = value
            conn.close()
            if cookies:
                return cookies
        except Exception:
            continue

    return cookies


def get_firefox_cookies(domain: str) -> dict:
    """Lê cookies do Firefox usando sqlite3"""
    firefox_paths = [
        Path.home() / ".mozilla" / "firefox",
        Path.home() / ".librewolf",
    ]

    for base in firefox_paths:
        if not base.exists():
            continue
        profiles = list(base.glob("*.default*"))
        for profile in profiles:
            cookie_path = profile / "cookies.sqlite"
            if not cookie_path.exists():
                continue
            try:
                conn = sqlite3.connect(str(cookie_path))
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT name, value FROM moz_cookies WHERE host LIKE ? AND name != ''",
                    (f"%{domain}",),
                )
                cookies = {row["name"]: row["value"] for row in cursor}
                conn.close()
                if cookies:
                    return cookies
            except Exception:
                continue

    return {}


def load_cookies(domain: str) -> tuple[dict, str]:
    """Tenta carregar cookies de vários navegadores"""
    try:
        import browser_cookie3

        for browser in ["brave", "chromium", "chrome"]:
            try:
                cj = getattr(browser_cookie3, browser)()
                cookies = {c.name: c.value for c in cj if domain in c.domain}
                if cookies.get("lastActiveOrg"):
                    return cookies, browser
            except Exception:
                continue
    except ImportError:
        pass

    cookies = get_chromium_cookies(domain)
    if cookies:
        return cookies, "chromium"

    cookies = get_firefox_cookies(domain)
    if cookies:
        return cookies, "firefox"

    raise RuntimeError(f"Failed to read cookies for {domain}")


def fetch_claude_usage() -> dict:
    """Faz request para API do Claude usando curl"""
    try:
        cookies, browser = load_cookies(CLAUDE_DOMAIN)
    except Exception as e:
        raise RuntimeError(f"Failed to read cookies: {e}")

    org_id = cookies.get("lastActiveOrg")
    if not org_id:
        raise RuntimeError(
            "Missing 'lastActiveOrg' in cookies. Please refresh Claude page in browser or switch Organization."
        )

    url = f"https://{CLAUDE_DOMAIN}/api/organizations/{org_id}/usage"

    cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())

    cmd = [
        "curl",
        "-s",
        "-m",
        "10",
        "-H",
        f"Cookie: {cookie_header}",
        "-H",
        "Referer: https://claude.ai/chats",
        "-H",
        "Accept: application/json, text/plain, */*",
        "-H",
        "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        url,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            raise RuntimeError(f"curl failed: {result.stderr}")
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON response: {e}")
    except Exception as e:
        raise RuntimeError(f"Request failed: {e}")


def get_cached_usage() -> dict:
    """Get from cache or fetch"""
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    if CACHE_FILE.exists():
        age = time.time() - CACHE_FILE.stat().st_mtime
        if age < CACHE_TTL:
            try:
                with open(CACHE_FILE) as f:
                    return json.load(f)
            except Exception:
                pass

    data = fetch_claude_usage()
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

    return data


def format_eta(reset_at: str | int | None) -> str:
    """Format ETA"""
    if not reset_at:
        return "0m00s"

    try:
        from datetime import datetime, timezone

        if isinstance(reset_at, str):
            if reset_at.endswith("Z"):
                reset_at = reset_at[:-1] + "+00:00"
            reset_dt = datetime.fromisoformat(reset_at)
        else:
            reset_dt = datetime.fromtimestamp(reset_at, tz=timezone.utc)

        now = datetime.now(timezone.utc)
        delta = reset_dt - now
    except Exception:
        return "??m??"

    secs = int(delta.total_seconds())
    if secs <= 0:
        return "0m00s"

    if secs >= 86400:
        days = secs // 86400
        hours = (secs % 86400) // 3600
        return f"{days}d{hours:02h}"

    if secs >= 3600:
        hours = secs // 3600
        mins = (secs % 3600) // 60
        return f"{hours}h{mins:02m}"

    mins = secs // 60
    secs_rem = secs % 60
    return f"{mins}m{secs_rem:02s}"


def parse_window(usage: dict, key: str) -> tuple[float, str | None]:
    """Parse window usage"""
    raw = usage.get(key) or {}
    util = raw.get("utilization", 0)
    resets_at = raw.get("resets_at")

    try:
        util_f = float(util)
    except Exception:
        util_f = 0.0

    return util_f, resets_at


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--waybar", action="store_true")
    parser.add_argument("--format", type=str, default=None)
    args = parser.parse_args()

    try:
        usage = get_cached_usage()
    except Exception as e:
        if args.waybar:
            print(
                json.dumps(
                    {
                        "text": f"<span foreground='#ff5555'>󰜡 Err</span>",
                        "tooltip": f"Error: {e}",
                        "class": "critical",
                    }
                )
            )
            return
        else:
            print(f"[!] Error: {e}", file=sys.stderr)
            return

    fh, fh_reset = parse_window(usage, "five_hour")
    sd, sd_reset = parse_window(usage, "seven_day")

    fh_pct = int(round(fh))
    sd_pct = int(round(sd))

    fh_reset_str = format_eta(fh_reset) if fh_reset else "Not started"
    sd_reset_str = format_eta(sd_reset) if sd_reset else "Not started"

    if sd_pct >= 100:
        pct = sd_pct
        reset_str = sd_reset_str
        win_name = "7d"
        status = "Pause"
    elif sd_pct > 80:
        pct = sd_pct
        reset_str = sd_reset_str
        win_name = "7d"
        status = ""
    else:
        pct = fh_pct
        reset_str = fh_reset_str
        win_name = "5h"
        status = "" if pct > 0 else "Ready"

    icon = "󰜡"

    if args.format:
        text = args.format.replace("{icon_plain}", icon).replace("{pct}", f"{pct}%")
    else:
        text = f"{icon} {pct}%"
        if status:
            text = f"{icon} {status}"

    tooltip = (
        "Window     Used    Reset\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"5-Hour     {fh:>3.0f}%    {fh_reset_str}\n"
        f"7-Day      {sd:>3.0f}%    {sd_reset_str}\n"
        "\n"
        "Click to Refresh"
    )

    if pct < 50:
        cls = "claude-low"
    elif pct < 80:
        cls = "claude-mid"
    else:
        cls = "claude-high"

    output = {
        "text": text,
        "tooltip": tooltip,
        "class": cls,
        "alt": win_name,
        "percentage": pct,
    }

    print(json.dumps(output))


if __name__ == "__main__":
    main()
