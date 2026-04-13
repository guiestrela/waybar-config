#!/usr/bin/env python3
"""
Opencode usage - standalone sem dependências externas
Usa o comando 'opencode stats' para buscar dados
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path


ICON = "⌬"
CACHE_FILE = Path.home() / ".cache" / "waybar-ai-usage" / "opencode.json"
CACHE_TTL = 120


def _parse_stats_text(output: str) -> dict:
    stats = {
        "sessions": 0,
        "messages": 0,
        "days": 0,
        "total_cost": 0.0,
        "avg_cost_day": 0.0,
        "avg_tokens_session": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read": 0,
        "cache_write": 0,
    }

    lines = output.split("\n")

    for line in lines:
        line = line.strip()

        if "Sessions" in line:
            try:
                stats["sessions"] = int(re.search(r"Sessions\s+(\d+)", line).group(1))
            except (AttributeError, ValueError):
                pass

        if "Messages" in line:
            try:
                stats["messages"] = int(re.search(r"Messages\s+(\d+)", line).group(1))
            except (AttributeError, ValueError):
                pass

        if "Days" in line:
            try:
                stats["days"] = int(re.search(r"Days\s+(\d+)", line).group(1))
            except (AttributeError, ValueError):
                pass

        if "Total Cost" in line:
            try:
                cost_str = re.search(r"\$?([\d.]+)", line).group(1)
                stats["total_cost"] = float(cost_str)
            except (AttributeError, ValueError):
                pass

        if "Avg Cost/Day" in line:
            try:
                cost_str = re.search(r"\$?([\d.]+)", line).group(1)
                stats["avg_cost_day"] = float(cost_str)
            except (AttributeError, ValueError):
                pass

        if "Avg Tokens/Session" in line:
            try:
                tokens_str = re.search(r"([\d.]+)([KM]?)", line)
                value = float(tokens_str.group(1))
                suffix = tokens_str.group(2)
                if suffix == "K":
                    value *= 1000
                elif suffix == "M":
                    value *= 1000000
                stats["avg_tokens_session"] = int(value)
            except (AttributeError, ValueError):
                pass

        if "Input" in line and "Cache" not in line:
            try:
                tokens_str = re.search(r"([\d.]+)([KM]?)", line)
                value = float(tokens_str.group(1))
                suffix = tokens_str.group(2)
                if suffix == "K":
                    value *= 1000
                elif suffix == "M":
                    value *= 1000000
                stats["input_tokens"] = int(value)
            except (AttributeError, ValueError):
                pass

        if "Output" in line and "Cache" not in line:
            try:
                tokens_str = re.search(r"([\d.]+)([KM]?)", line)
                value = float(tokens_str.group(1))
                suffix = tokens_str.group(2)
                if suffix == "K":
                    value *= 1000
                elif suffix == "M":
                    value *= 1000000
                stats["output_tokens"] = int(value)
            except (AttributeError, ValueError):
                pass

        if "Cache Read" in line:
            try:
                tokens_str = re.search(r"([\d.]+)([KM]?)", line)
                value = float(tokens_str.group(1))
                suffix = tokens_str.group(2)
                if suffix == "K":
                    value *= 1000
                elif suffix == "M":
                    value *= 1000000
                stats["cache_read"] = int(value)
            except (AttributeError, ValueError):
                pass

        if "Cache Write" in line:
            try:
                tokens_str = re.search(r"([\d.]+)([KM]?)", line)
                value = float(tokens_str.group(1))
                suffix = tokens_str.group(2)
                if suffix == "K":
                    value *= 1000
                elif suffix == "M":
                    value *= 1000000
                stats["cache_write"] = int(value)
            except (AttributeError, ValueError):
                pass

    return stats


def _fetch_stats_uncached() -> dict:
    try:
        result = subprocess.run(
            ["opencode", "stats"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if stderr:
                raise RuntimeError(stderr)
            raise RuntimeError(f"Command failed with exit code {result.returncode}")
        return _parse_stats_text(result.stdout)
    except FileNotFoundError:
        raise RuntimeError("opencode command not found. Is it installed?")


def get_opencode_usage() -> dict:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    if CACHE_FILE.exists():
        age = time.time() - CACHE_FILE.stat().st_mtime
        if age < CACHE_TTL:
            try:
                with open(CACHE_FILE) as f:
                    return json.load(f)
            except Exception:
                pass

    data = _fetch_stats_uncached()
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

    return data


def print_waybar(
    stats: dict, format_str: str | None = None, tooltip_format: str | None = None
) -> None:
    sessions = stats.get("sessions", 0)
    messages = stats.get("messages", 0)
    days = stats.get("days", 0)
    total_cost = stats.get("total_cost", 0.0)
    avg_cost_day = stats.get("avg_cost_day", 0.0)
    avg_tokens = stats.get("avg_tokens_session", 0)
    input_tokens = stats.get("input_tokens", 0)
    output_tokens = stats.get("output_tokens", 0)
    cache_read = stats.get("cache_read", 0)
    cache_write = stats.get("cache_write", 0)

    icon_styled = f"<span>{ICON}</span>"

    data = {
        "sessions": sessions,
        "messages": messages,
        "days": days,
        "total_cost": f"{total_cost:.2f}",
        "avg_cost_day": f"{avg_cost_day:.2f}",
        "avg_tokens": avg_tokens,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read": cache_read,
        "cache_write": cache_write,
        "icon": icon_styled,
        "icon_plain": ICON,
    }

    if format_str:
        text = format_str.format(**data)
    else:
        if sessions > 0:
            text = f"{icon_styled} {sessions}s"
        else:
            text = f"{icon_styled}"

    if tooltip_format:
        tooltip = tooltip_format.format(**data)
    else:
        tooltip = (
            "Opencode Stats\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"Sessions:    {sessions}\n"
            f"Messages:    {messages}\n"
            f"Days:        {days}\n"
            "───────────────────\n"
            f"Total Cost:  ${total_cost:.2f}\n"
            f"Avg/Day:     ${avg_cost_day:.2f}\n"
            "───────────────────\n"
            f"Avg Tokens:  {avg_tokens:,}\n"
            f"Input:       {input_tokens:,}\n"
            f"Output:      {output_tokens:,}\n"
            f"Cache Read:  {cache_read:,}\n"
            f"Cache Write: {cache_write:,}\n"
            "\nClick to Refresh"
        )

    output = {
        "text": text,
        "tooltip": tooltip,
        "class": "opencode",
    }

    print(json.dumps(output))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--waybar", action="store_true", help="Output in JSON format for Waybar"
    )
    parser.add_argument("--format", type=str, default=None, help="Custom format string")
    parser.add_argument(
        "--tooltip-format", type=str, default=None, help="Custom tooltip format"
    )
    args = parser.parse_args()

    try:
        stats = get_opencode_usage()
    except Exception as e:
        if args.waybar:
            print(
                json.dumps(
                    {
                        "text": f"<span foreground='#ff5555'>{ICON}</span> Err",
                        "tooltip": f"Error fetching opencode stats:\n{e}",
                        "class": "critical",
                    }
                )
            )
            sys.exit(0)
        else:
            print(f"[!] Critical Error: {e}", file=sys.stderr)
            sys.exit(1)

    if args.waybar:
        print_waybar(stats, args.format, args.tooltip_format)
    else:
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
