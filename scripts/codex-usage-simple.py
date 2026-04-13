#!/usr/bin/env python3
"""
Codex usage - tenta API primeiro, fallback para CLI
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


CODEX_DOMAIN = "chatgpt.com"
CACHE_FILE = Path.home() / ".cache" / "waybar-ai-usage" / "codex.json"
CACHE_TTL = 120
CODEX_SESSIONS_DIR = Path.home() / ".codex" / "sessions"


def get_openai_api_key() -> str | None:
    """Lê token de configuração"""
    config_paths = [
        Path.home() / ".config" / "waybar-ai-usage" / "codex.conf",
        Path.home() / ".config" / "waybar" / "codex.conf",
    ]
    for config_path in config_paths:
        if config_path.exists():
            content = config_path.read_text().strip()
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    if key.strip() == "OPENAI_API_KEY":
                        return value.strip()
    return os.environ.get("OPENAI_API_KEY")


def get_chromium_cookies(domain: str) -> dict:
    """Lê cookies do Chromium"""
    cookie_paths = [
        Path.home() / ".config" / "chromium" / "Default" / "Cookies",
        Path.home() / ".config" / "chrome" / "Default" / "Cookies",
    ]

    for cookie_path in cookie_paths:
        if not cookie_path.exists():
            continue
        try:
            conn = sqlite3.connect(cookie_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT name, value FROM cookies WHERE host_key LIKE ? AND name != ''",
                (f"%{domain}",),
            )
            cookies = {row["name"]: row["value"] for row in cursor}
            conn.close()
            if cookies:
                return cookies
        except Exception:
            continue
    return {}


def _format_reset_value(reset_at: int | str | None) -> str:
    if reset_at is None:
        return "N/A"
    return str(reset_at)


def _read_latest_rate_limits() -> dict | None:
    """Lê o último snapshot de rate limit gravado pelo Codex CLI."""
    if not CODEX_SESSIONS_DIR.exists():
        return None

    session_files = sorted(CODEX_SESSIONS_DIR.rglob("*.jsonl"), reverse=True)
    for session_file in session_files[:20]:
        try:
            lines = session_file.read_text().splitlines()
        except Exception:
            continue

        for line in reversed(lines):
            try:
                event = json.loads(line)
            except Exception:
                continue

            if event.get("type") != "event_msg":
                continue

            payload = event.get("payload") or {}
            if payload.get("type") != "token_count":
                continue

            rate_limits = payload.get("rate_limits") or {}
            primary = rate_limits.get("primary")
            secondary = rate_limits.get("secondary")
            if not primary and not secondary:
                continue

            return {
                "primary": primary or {},
                "secondary": secondary or {},
                "plan_type": rate_limits.get("plan_type"),
                "timestamp": event.get("timestamp"),
                "session_file": str(session_file),
            }

    return None


def fetch_via_local_codex_state() -> dict | None:
    """Usa os dados locais do Codex CLI, sem depender de rede."""
    rate_limits = _read_latest_rate_limits()
    if not rate_limits:
        return None

    primary = rate_limits.get("primary") or {}
    secondary = rate_limits.get("secondary") or {}

    primary_pct = int(round(float(primary.get("used_percent") or 0)))
    secondary_pct = int(round(float(secondary.get("used_percent") or 0)))

    primary_minutes = int(primary.get("window_minutes") or 0)
    secondary_minutes = int(secondary.get("window_minutes") or 0)

    fh_pct = 0
    sd_pct = 0
    fh_reset = "N/A"
    sd_reset = "N/A"

    windows = [
        (primary_minutes, primary_pct, primary.get("resets_at")),
        (secondary_minutes, secondary_pct, secondary.get("resets_at")),
    ]

    for minutes, pct, reset_at in windows:
        if minutes <= 0:
            continue
        if minutes <= 5 * 60:
            fh_pct = pct
            fh_reset = _format_reset_value(reset_at)
        elif minutes >= 7 * 24 * 60:
            sd_pct = pct
            sd_reset = _format_reset_value(reset_at)

    if fh_pct == 0 and sd_pct == 0:
        if primary_minutes > 0:
            sd_pct = primary_pct
            sd_reset = _format_reset_value(primary.get("resets_at"))
        elif secondary_minutes > 0:
            sd_pct = secondary_pct
            sd_reset = _format_reset_value(secondary.get("resets_at"))

    pct = max(fh_pct, sd_pct, primary_pct, secondary_pct)

    return {
        "source": "local_codex",
        "percentage": pct,
        "fh_pct": fh_pct,
        "sd_pct": sd_pct or primary_pct or secondary_pct,
        "fh_reset": fh_reset,
        "sd_reset": sd_reset,
        "status": "limit_reached" if pct >= 100 else "ok",
        "plan_type": rate_limits.get("plan_type") or "unknown",
        "last_snapshot": rate_limits.get("timestamp"),
    }


def fetch_via_api() -> dict | None:
    """Tenta buscar via API com OpenAI API key"""
    api_key = get_openai_api_key()
    if not api_key:
        return None

    try:
        today = time.strftime("%Y-%m-%d")
        url = f"https://api.openai.com/v1/usage?date={today}"

        cmd = [
            "curl",
            "-s",
            "-m",
            "10",
            "-H",
            f"Authorization: Bearer {api_key}",
            "-H",
            "Accept: application/json",
            url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and result.stdout.strip().startswith("{"):
            data = json.loads(result.stdout)

            total_usage = data.get("total_usage", 0)
            usage_limit = data.get("usage_limit", 100_000_000)

            pct = int((total_usage / usage_limit) * 100) if usage_limit > 0 else 0

            return {
                "five_hour": {"utilization": pct, "resets_at": "N/A"},
                "seven_day": {"utilization": pct, "resets_at": "N/A"},
            }
    except Exception:
        pass
    return None


def fetch_via_cli() -> dict:
    """Fallback: usa codex CLI"""
    tmp_dir = tempfile.mkdtemp()
    subprocess.run(["git", "init"], cwd=tmp_dir, capture_output=True)

    cmd = [
        "codex",
        "exec",
        "--full-auto",
        "--",
        "query the API for current OpenAI Codex API usage quota and respond ONLY with a number from 0-100 representing percentage used, nothing else",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
            cwd=tmp_dir,
        )

        output = result.stdout + result.stderr

        if "usage limit" in output.lower() or "hit your" in output.lower():
            date_match = re.search(r"try again at (.+?)(?:\.|\\n|$)", output)
            reset_date = date_match.group(1).strip() if date_match else "N/A"
            return {
                "source": "cli",
                "status": "limit_reached",
                "message": output.strip(),
                "percentage": 100,
                "reset": reset_date,
            }

        pct = 0
        for line in output.split("\n"):
            if "%" in line:
                try:
                    numbers = "".join(filter(str.isdigit, line))
                    pct = int(numbers) if numbers else 0
                except Exception:
                    pass

        return {
            "source": "cli",
            "status": "ok",
            "message": output.strip()[:200],
            "percentage": pct,
            "reset": "N/A",
        }
    except subprocess.TimeoutExpired:
        return {
            "source": "cli",
            "status": "unavailable",
            "message": "Codex timeout - service unavailable",
            "percentage": 0,
            "reset": "N/A",
        }
    except Exception as e:
        return {
            "source": "cli",
            "status": "unavailable",
            "message": str(e),
            "percentage": 0,
            "reset": "N/A",
        }
    finally:
        try:
            import shutil

            shutil.rmtree(tmp_dir, ignore_errors=True)
        except:
            pass


def fetch_codex_usage() -> dict:
    """Usa estado local do Codex primeiro e só então faz fallbacks."""
    local_data = fetch_via_local_codex_state()
    if local_data:
        return local_data

    api_data = fetch_via_api()

    if api_data:
        five_hour = api_data.get("five_hour", {})
        seven_day = api_data.get("seven_day", {})

        fh_util = five_hour.get("utilization", 0)
        sd_util = seven_day.get("utilization", 0)

        pct = int(max(fh_util, sd_util))

        fh_reset = five_hour.get("resets_at", "N/A")
        sd_reset = seven_day.get("resets_at", "N/A")

        return {
            "source": "api",
            "percentage": pct,
            "fh_pct": int(fh_util),
            "sd_pct": int(sd_util),
            "fh_reset": fh_reset,
            "sd_reset": sd_reset,
            "status": "ok",
        }

    return fetch_via_cli()


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

    data = fetch_codex_usage()
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

    return data


def format_eta(reset_at: str | None) -> str:
    """Formata tempo restante"""
    if not reset_at or reset_at == "N/A":
        return "N/A"

    try:
        if re.fullmatch(r"\d+", str(reset_at)):
            reset_dt = datetime.fromtimestamp(int(str(reset_at)), tz=timezone.utc)
            local_dt = reset_dt.astimezone()
            return local_dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        pass

    return str(reset_at)


def format_renew_date(reset_at: str | None) -> str:
    """Formata a data de renovacao a partir de ISO/timestamp textual quando possivel."""
    if not reset_at or reset_at == "N/A":
        return "N/A"

    try:
        normalized = reset_at
        if isinstance(normalized, str) and normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"

        if isinstance(normalized, str) and re.fullmatch(r"\d+", normalized):
            reset_dt = datetime.fromtimestamp(int(normalized), tz=timezone.utc)
        else:
            reset_dt = datetime.fromisoformat(str(normalized))
            if reset_dt.tzinfo is None:
                reset_dt = reset_dt.replace(tzinfo=timezone.utc)

        local_dt = reset_dt.astimezone()
        return local_dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(reset_at)


def print_waybar(usage: dict, format_str: str | None = None) -> None:
    pct = usage.get("percentage", 0)
    fh_pct = int(usage.get("fh_pct", 0) or 0)
    sd_pct = int(usage.get("sd_pct", 0) or 0)
    status = usage.get("status", "unknown")
    source = usage.get("source", "unknown")
    fh_reset = format_eta(usage.get("fh_reset"))
    sd_reset = format_eta(usage.get("sd_reset"))
    renew_date = format_renew_date(usage.get("sd_reset")) or "N/A"

    if status == "limit_reached":
        fh_reset = "Limited"
        sd_reset = format_eta(usage.get("reset"))
        renew_date = format_renew_date(usage.get("reset"))

    icon = "󰬫"
    icon_styled = f"<span>{icon}</span>"

    data = {
        "pct": pct,
        "icon": icon_styled,
        "icon_plain": icon,
        "status": status,
        "source": source,
        "fh_reset": fh_reset,
        "sd_reset": sd_reset,
    }

    if format_str:
        text = format_str.format(**data)
    else:
        text = f"{icon_styled} {pct}%"

    if status == "limit_reached":
        cls = "codex-high"
    elif status == "unavailable":
        cls = "codex-unavailable"
    elif status == "error":
        cls = "critical"
    else:
        if pct < 50:
            cls = "codex-low"
        elif pct < 80:
            cls = "codex-mid"
        else:
            cls = "codex-high"

    tooltip = (
        "Window     Used    Reset\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"5-Hour     {fh_pct}%    {fh_reset}\n"
        f"7-Day      {sd_pct}%    {sd_reset}\n"
        f"\nRenews: {renew_date}\n"
        f"\nSource: {source}\n"
        "Click to Refresh"
    )

    output = {"text": text, "tooltip": tooltip, "class": cls, "percentage": pct}
    print(json.dumps(output))


def main() -> None:
    import argparse
    import sys

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
                        "text": f"<span foreground='#ff5555'>󰬫 Err</span>",
                        "tooltip": f"Error: {e}",
                        "class": "critical",
                    }
                )
            )
            return
        else:
            print(f"[!] Error: {e}", file=sys.stderr)
            return

    if args.waybar:
        print_waybar(usage, args.format)
    else:
        print(json.dumps(usage))


if __name__ == "__main__":
    main()
