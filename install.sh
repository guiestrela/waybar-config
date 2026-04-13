#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WAYBAR_DIR="${HOME}/.config/waybar"
WAYBAR_SCRIPTS_DIR="${WAYBAR_DIR}/scripts"
AI_CONFIG_DIR="${HOME}/.config/waybar-ai-usage"
BACKUP_DIR="${WAYBAR_DIR}/backup-$(date +%Y%m%d-%H%M%S)"

INSTALL_DEPS=0
RESTART_WAYBAR=1

print_help() {
  cat <<'EOF'
Usage: ./install.sh [options]

Options:
  --install-deps   Install common dependencies (Arch/pacman only)
  --no-restart     Do not restart Waybar after install
  -h, --help       Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-deps)
      INSTALL_DEPS=1
      shift
      ;;
    --no-restart)
      RESTART_WAYBAR=0
      shift
      ;;
    -h|--help)
      print_help
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      print_help
      exit 1
      ;;
  esac
done

if [[ ! -f "${SCRIPT_DIR}/config.jsonc" || ! -f "${SCRIPT_DIR}/style.css" ]]; then
  echo "Run this script from the waybar-config directory."
  exit 1
fi

if [[ "${INSTALL_DEPS}" -eq 1 ]]; then
  if command -v pacman >/dev/null 2>&1; then
    sudo pacman -S --needed --noconfirm \
      waybar hyprland pulseaudio brightnessctl bluez bluez-utils \
      networkmanager power-profiles-daemon btop python jq
  else
    echo "Skipping dependency install: only pacman is supported by --install-deps."
  fi
fi

mkdir -p "${WAYBAR_DIR}" "${WAYBAR_SCRIPTS_DIR}" "${AI_CONFIG_DIR}" "${BACKUP_DIR}"

for file in config.jsonc style.css; do
  if [[ -f "${WAYBAR_DIR}/${file}" ]]; then
    cp -f "${WAYBAR_DIR}/${file}" "${BACKUP_DIR}/${file}"
  fi
done

cp -f "${SCRIPT_DIR}/config.jsonc" "${WAYBAR_DIR}/config.jsonc"
cp -f "${SCRIPT_DIR}/style.css" "${WAYBAR_DIR}/style.css"
cp -f "${SCRIPT_DIR}/scripts/"* "${WAYBAR_SCRIPTS_DIR}/"
cp -f "${SCRIPT_DIR}/ai-config/"*.example "${AI_CONFIG_DIR}/"

if [[ ! -f "${AI_CONFIG_DIR}/copilot.conf" && -f "${AI_CONFIG_DIR}/copilot.conf.example" ]]; then
  cp -f "${AI_CONFIG_DIR}/copilot.conf.example" "${AI_CONFIG_DIR}/copilot.conf"
fi

if [[ ! -f "${AI_CONFIG_DIR}/codex.conf" && -f "${AI_CONFIG_DIR}/codex.conf.example" ]]; then
  cp -f "${AI_CONFIG_DIR}/codex.conf.example" "${AI_CONFIG_DIR}/codex.conf"
fi

chmod +x "${WAYBAR_SCRIPTS_DIR}/"*.sh "${WAYBAR_SCRIPTS_DIR}/"*.py

if [[ "${RESTART_WAYBAR}" -eq 1 ]]; then
  if command -v omarchy-restart-waybar >/dev/null 2>&1; then
    omarchy-restart-waybar
  else
    pids="$(pgrep -x waybar || true)"
    if [[ -n "${pids}" ]]; then
      while IFS= read -r pid; do
        [[ -n "${pid}" ]] && kill "${pid}"
      done <<< "${pids}"
    fi
    nohup waybar >/dev/null 2>&1 &
  fi
fi

cat <<EOF
Done.
- Backup: ${BACKUP_DIR}
- Installed: ${WAYBAR_DIR}/config.jsonc
- Installed: ${WAYBAR_DIR}/style.css
- Scripts: ${WAYBAR_SCRIPTS_DIR}
- AI config: ${AI_CONFIG_DIR}

Next:
1. Edit ${AI_CONFIG_DIR}/copilot.conf
2. Edit ${AI_CONFIG_DIR}/codex.conf (optional)
EOF
