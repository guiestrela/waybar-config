#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_WAYBAR_DIR="${HOME}/.config/waybar"
SRC_SCRIPTS_DIR="${SRC_WAYBAR_DIR}/scripts"
SRC_AI_DIR="${HOME}/.config/waybar-ai-usage"

BACKUP_ROOT="${SCRIPT_DIR}/backups"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${BACKUP_ROOT}/${STAMP}"

INCLUDE_SECRETS=0

print_help() {
  cat <<'EOF'
Usage: ./backup-and-update-repo.sh [options]

Options:
  --include-secrets  Also copy copilot.conf and codex.conf (careful with git)
  -h, --help         Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --include-secrets)
      INCLUDE_SECRETS=1
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

for required in "${SRC_WAYBAR_DIR}/config.jsonc" "${SRC_WAYBAR_DIR}/style.css"; do
  if [[ ! -f "${required}" ]]; then
    echo "Missing source file: ${required}" >&2
    exit 1
  fi
done

mkdir -p "${BACKUP_DIR}/scripts" "${BACKUP_DIR}/ai-config"

# 1) Backup current repository files
cp -f "${SCRIPT_DIR}/config.jsonc" "${BACKUP_DIR}/config.jsonc" 2>/dev/null || true
cp -f "${SCRIPT_DIR}/style.css" "${BACKUP_DIR}/style.css" 2>/dev/null || true
cp -f "${SCRIPT_DIR}/README.md" "${BACKUP_DIR}/README.md" 2>/dev/null || true
cp -f "${SCRIPT_DIR}/install.sh" "${BACKUP_DIR}/install.sh" 2>/dev/null || true
cp -f "${SCRIPT_DIR}/scripts/"* "${BACKUP_DIR}/scripts/" 2>/dev/null || true
cp -f "${SCRIPT_DIR}/ai-config/"* "${BACKUP_DIR}/ai-config/" 2>/dev/null || true

# 2) Update repository from active ~/.config files
cp -f "${SRC_WAYBAR_DIR}/config.jsonc" "${SCRIPT_DIR}/config.jsonc"
cp -f "${SRC_WAYBAR_DIR}/style.css" "${SCRIPT_DIR}/style.css"

mkdir -p "${SCRIPT_DIR}/scripts" "${SCRIPT_DIR}/ai-config"
cp -f "${SRC_SCRIPTS_DIR}/"*.sh "${SCRIPT_DIR}/scripts/" 2>/dev/null || true
cp -f "${SRC_SCRIPTS_DIR}/"*.py "${SCRIPT_DIR}/scripts/" 2>/dev/null || true

if [[ -f "${SRC_AI_DIR}/copilot.conf.example" ]]; then
  cp -f "${SRC_AI_DIR}/copilot.conf.example" "${SCRIPT_DIR}/ai-config/copilot.conf.example"
fi

if [[ -f "${SRC_AI_DIR}/codex.conf.example" ]]; then
  cp -f "${SRC_AI_DIR}/codex.conf.example" "${SCRIPT_DIR}/ai-config/codex.conf.example"
fi

if [[ "${INCLUDE_SECRETS}" -eq 1 ]]; then
  [[ -f "${SRC_AI_DIR}/copilot.conf" ]] && cp -f "${SRC_AI_DIR}/copilot.conf" "${SCRIPT_DIR}/ai-config/copilot.conf"
  [[ -f "${SRC_AI_DIR}/codex.conf" ]] && cp -f "${SRC_AI_DIR}/codex.conf" "${SCRIPT_DIR}/ai-config/codex.conf"
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
- Backup created: ${BACKUP_DIR}
- Repo updated from: ${SRC_WAYBAR_DIR}
- AI source: ${SRC_AI_DIR}
EOF
