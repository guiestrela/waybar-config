#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_WAYBAR_DIR="${HOME}/.config/waybar"
SRC_SCRIPTS_DIR="${SRC_WAYBAR_DIR}/scripts"
SRC_AI_DIR="${HOME}/.config/waybar-ai-usage"

print_help() {
  cat <<'EOF'
Usage: ./backup-and-update-repo.sh [options]

Options:
  -h, --help         Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      print_help
      exit 0
      ;;
    --include-secrets)
      echo "Option not supported anymore: --include-secrets" >&2
      echo "Use only *.example files to avoid leaking secrets to git." >&2
      exit 1
      ;;
    *)
      echo "Unknown option: $1" >&2
      print_help
      exit 1
      ;;
  esac
done

for required in "${SRC_WAYBAR_DIR}/config.jsonc" "${SRC_WAYBAR_DIR}/style.css"; do
  if [[ ! -f "${required}" ]]; then
    echo "Missing source file: ${required}" >&2
    exit 1
  fi
done

# Update repository from active ~/.config files
cp -f "${SRC_WAYBAR_DIR}/config.jsonc" "${SCRIPT_DIR}/config.jsonc"
cp -f "${SRC_WAYBAR_DIR}/style.css" "${SCRIPT_DIR}/style.css"

mkdir -p "${SCRIPT_DIR}/scripts" "${SCRIPT_DIR}/ai-config"
cp -f "${SRC_SCRIPTS_DIR}/"*.sh "${SCRIPT_DIR}/scripts/" 2>/dev/null || true
cp -f "${SRC_SCRIPTS_DIR}/"*.py "${SCRIPT_DIR}/scripts/" 2>/dev/null || true
cp -f "${SRC_SCRIPTS_DIR}/"*.example "${SCRIPT_DIR}/scripts/" 2>/dev/null || true

if [[ -f "${SRC_AI_DIR}/copilot.conf.example" ]]; then
  cp -f "${SRC_AI_DIR}/copilot.conf.example" "${SCRIPT_DIR}/ai-config/copilot.conf.example"
fi

if [[ -f "${SRC_AI_DIR}/codex.conf.example" ]]; then
  cp -f "${SRC_AI_DIR}/codex.conf.example" "${SCRIPT_DIR}/ai-config/codex.conf.example"
fi

chmod +x "${SCRIPT_DIR}/install.sh" "${SCRIPT_DIR}/backup-and-update-repo.sh"
chmod +x "${SCRIPT_DIR}/scripts/"*.sh "${SCRIPT_DIR}/scripts/"*.py 2>/dev/null || true

if command -v git >/dev/null 2>&1 && git -C "${SCRIPT_DIR}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo
  echo "Git status:"
  git -C "${SCRIPT_DIR}" --no-pager status --short
fi

cat <<EOF
Done.
- Repo updated from: ${SRC_WAYBAR_DIR}
- AI source: ${SRC_AI_DIR}
EOF
