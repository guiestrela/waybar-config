#!/usr/bin/env python3

from __future__ import annotations

import json
import shutil
import urllib.error
import urllib.request


OLLAMA_ICON = "󰳆"
LOCAL_TAGS_URL = "http://localhost:11434/api/tags"
LOCAL_PS_URL = "http://localhost:11434/api/ps"
REMOTE_TAGS_URL = "https://ollama.com/api/tags"


def emit(text: str, tooltip: str, cls: str) -> None:
    print(json.dumps({"text": text, "tooltip": tooltip, "class": cls}))


def build_tooltip(lines: list[str], footer: str = "Click to Refresh") -> str:
    return "\n".join([*lines, "", footer])


def fetch_api_models(url: str) -> list[str]:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "waybar-ollama-status",
        },
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        payload = json.load(response)

    models = payload.get("models", [])
    names: list[str] = []
    for model in models:
        if not isinstance(model, dict):
            continue
        name = model.get("name") or model.get("model")
        if isinstance(name, str) and name.strip():
            names.append(name.strip())
    return names


def main() -> None:
    if shutil.which("ollama") is None:
        emit(
            f"{OLLAMA_ICON} N/A",
            build_tooltip(
                [
                    "Item       State",
                    "━━━━━━━━━━━━━━━━━━",
                    "Ollama     Missing",
                ]
            ),
            "critical",
        )
        return

    remote_models: list[str] = []
    remote_error: str | None = None
    try:
        remote_models = fetch_api_models(REMOTE_TAGS_URL)
    except urllib.error.URLError as exc:
        remote_error = str(exc.reason)
    except Exception as exc:
        remote_error = str(exc)

    try:
        models = fetch_api_models(LOCAL_TAGS_URL)
    except Exception as exc:
        emit(
            f"{OLLAMA_ICON} Err",
            build_tooltip(
                [
                    "Item       State",
                    "━━━━━━━━━━━━━━━━━━",
                    "Ollama     Error",
                    "",
                    str(exc),
                ]
            ),
            "critical",
        )
        return

    count = len(models)

    try:
        running_models = fetch_api_models(LOCAL_PS_URL)
    except Exception:
        running_models = []
    running_count = len(running_models)
    remote_count = len(remote_models)
    remote_info = f"{remote_count}       Cloud" if remote_error is None else "N/A      Unavailable"

    if count == 0:
        emit(
            f"{OLLAMA_ICON} 0+{remote_count}" if remote_error is None else f"{OLLAMA_ICON} 0",
            build_tooltip(
                [
                    "Item       Value    Info",
                    "━━━━━━━━━━━━━━━━━━━━━━━━━",
                    "Ollama     On       Local",
                    "Local      0        Empty",
                    f"Online     {remote_info}",
                    "Active     0        None",
                ]
                + ([f"", f"Remote err: {remote_error}"] if remote_error else [])
            ),
            "ollama-empty",
        )
        return

    preview = "\n".join(models[:6])
    more = f"\n... e mais {count - 6}" if count > 6 else ""
    active = running_models[0] if running_models else "None"
    emit(
        f"{OLLAMA_ICON} {count}+{remote_count}" if remote_error is None else f"{OLLAMA_ICON} {count}",
        build_tooltip(
            [
                "Item       Value    Info",
                "━━━━━━━━━━━━━━━━━━━━━━━━━",
                "Ollama     On       Local",
                f"Local      {count}        Ready",
                f"Online     {remote_info}",
                f"Active     {running_count}        {active}",
                "",
                preview + more,
            ]
            + ([f"", f"Remote err: {remote_error}"] if remote_error else [])
        ),
        "ollama-ready",
    )


if __name__ == "__main__":
    main()
