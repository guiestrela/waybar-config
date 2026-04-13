#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
from html import escape
from pathlib import Path


CLAUDE_CMD = [
    str(Path.home() / ".local" / "bin" / "claude-usage"),
    "--waybar",
    "--browser",
    "chromium",
    "--browser",
    "brave",
]

CODEX_CMD = [
    str(Path.home() / ".local" / "bin" / "codex-usage"),
    "--waybar",
    "--browser",
    "chromium",
    "--browser",
    "brave",
]

COPILOT_CMD = [
    str(Path.home() / ".local" / "bin" / "copilot-usage"),
    "--waybar",
]


def _run_json(cmd: list[str]) -> dict:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15, check=False)
    except Exception as exc:
        return {"text": "Err", "tooltip": f"Failed to run {' '.join(cmd)}\n{exc}", "class": "critical"}

    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or f"exit {proc.returncode}"
        return {"text": "Err", "tooltip": detail, "class": "critical"}

    try:
        return json.loads(proc.stdout)
    except Exception as exc:
        return {"text": "Err", "tooltip": f"Invalid JSON from {' '.join(cmd)}\n{exc}", "class": "critical"}


def _combined_class(*states: str) -> str:
    if any("critical" in s or "high" in s for s in states):
        return "ai-usage-high"
    if any("mid" in s for s in states):
        return "ai-usage-mid"
    return "ai-usage-low"


def main() -> None:
    claude = _run_json(CLAUDE_CMD)
    codex = _run_json(CODEX_CMD)
    copilot = _run_json(COPILOT_CMD)

    claude_pct = claude.get("percentage")
    codex_pct = codex.get("percentage")
    copilot_pct = copilot.get("percentage")

    claude_text = f"{claude_pct}%" if isinstance(claude_pct, int) else "Err"
    codex_text = f"{codex_pct}%" if isinstance(codex_pct, int) else "Err"
    copilot_text = f"{copilot_pct}%" if isinstance(copilot_pct, int) else "Err"

    tooltip = (
        "Claude\n"
        f"{escape(str(claude.get('tooltip', 'Unavailable')))}\n\n"
        "Codex\n"
        f"{escape(str(codex.get('tooltip', 'Unavailable')))}\n\n"
        "Copilot\n"
        f"{escape(str(copilot.get('tooltip', 'Unavailable')))}"
    )

    output = {
        "text": f"󰜡 {claude_text}  󰬫 {codex_text}   {copilot_text}",
        "tooltip": tooltip,
        "class": _combined_class(
            str(claude.get("class", "")),
            str(codex.get("class", "")),
            str(copilot.get("class", "")),
        ),
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
