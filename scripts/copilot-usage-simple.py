#!/usr/bin/env python3
"""
Copilot usage - sem dependências externas
Usa token de configuração + curl para API do GitHub
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


CACHE_FILE = Path.home() / ".cache" / "waybar-ai-usage" / "copilot.json"
CACHE_TTL = 60


def _next_month_reset_date() -> str:
    """Return formatted date for the 1st of next month (e.g., '01/05')."""
    now = datetime.now(timezone.utc)
    if now.month == 12:
        reset = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        reset = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
    return reset.strftime("%d/%m")


def get_token() -> str:
    """Lê token de configuração"""
    config_paths = [
        Path.home() / ".config" / "waybar-ai-usage" / "copilot.conf",
        Path.home() / ".config" / "waybar" / "copilot.conf",
    ]

    for config_path in config_paths:
        if config_path.exists():
            content = config_path.read_text().strip()
            if not content:
                continue
            if content.startswith("GITHUB_TOKEN="):
                token = content.split("=", 1)[1].strip()
                if token:
                    return token
            elif content.startswith("github_pat_"):
                return content

    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        return token

    raise RuntimeError(
        "No token found. Create ~/.config/waybar-ai-usage/copilot.conf with your Fine-grained PAT"
    )


def get_username() -> str:
    """Get current username"""
    return os.environ.get("USER", os.environ.get("USERNAME", "unknown"))


def fetch_copilot_usage() -> dict:
    """Faz request para API do Copilot usando curl"""
    token = get_token()
    username = get_username()

    url = f"https://api.github.com/users/{username}/settings/billing/premium_request/usage"

    cmd = [
        "curl",
        "-s",
        "-m",
        "10",
        "-H",
        f"Authorization: Bearer {token}",
        "-H",
        "Accept: application/vnd.github+json",
        "-H",
        "X-GitHub-Api-Version: 2022-11-28",
        "-H",
        "User-Agent: Mozilla/5.0",
        url,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            raise RuntimeError(f"curl failed: {result.stderr}")

        data = json.loads(result.stdout)

        if "error" in data:
            raise RuntimeError(f"API error: {data.get('message', 'Unknown')}")

        return data
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

    data = fetch_copilot_usage()
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

    return data


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
                        "text": f"<span foreground='#ff5555'> Err</span>",
                        "tooltip": f"Error: {e}",
                        "class": "critical",
                    }
                )
            )
            return
        else:
            print(f"[!] Error: {e}", file=sys.stderr)
            return

    usage_items = usage.get("usageItems", [])
    total_requests = sum(item.get("grossQuantity", 0) for item in usage_items)
    total_requests = int(total_requests)

    month = usage.get("timePeriod", {}).get("month", "")
    year = usage.get("timePeriod", {}).get("year", "")

    ALLOWANCE = 300
    pct = int((total_requests / ALLOWANCE) * 100)

    icon = ""

    if args.format:
        text = args.format.replace("{icon_plain}", icon).replace("{pct}", f"{pct}%")
    else:
        text = f"{icon} {pct}%"

    models = {}
    for item in usage_items:
        model = item.get("model", "Unknown")
        qty = int(item.get("grossQuantity", 0))
        if qty > 0:
            models[model] = qty

    models_str = (
        "\n".join(f"  {m}: {q}" for m, q in sorted(models.items(), key=lambda x: -x[1]))
        if models
        else "  No usage"
    )

    reset_date = _next_month_reset_date()

    tooltip = (
        f"GitHub Copilot ({month}/{year})\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Premium Requests: {total_requests}\n"
        f"\n{models_str}\n"
        f"\nRenews: {reset_date} of each month\n"
        "\nClick to Refresh"
    )

    if pct < 50:
        cls = "copilot-low"
    elif pct < 80:
        cls = "copilot-mid"
    else:
        cls = "copilot-high"

    output = {"text": text, "tooltip": tooltip, "class": cls, "percentage": pct}

    print(json.dumps(output))


if __name__ == "__main__":
    main()
