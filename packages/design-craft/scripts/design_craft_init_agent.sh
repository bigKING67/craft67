#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_SKILL="${ROOT_DIR}/skills/design-craft"
AGENT=""
TARGET="${PWD}"
SCOPE="project"
MODE="copy"
WITH_RULE=0
DRY_RUN=0
FORCE=0

usage() {
  cat <<'EOF'
Usage:
  scripts/design_craft_init_agent.sh --agent codex|claude|cursor|pi|generic [options]

Options:
  --target <path>       Project path for project installs, or home path for user installs.
  --scope <value>       project|user (default: project)
  --mode <value>        copy|symlink (default: copy)
  --with-rule           Also install the optional Cursor rule template.
  --dry-run             Print actions without writing files.
  --force               Backup an existing target before installing.
EOF
}

abspath() {
  local resolved
  resolved="$(python3 - "$1" <<'PY'
import sys
from pathlib import Path
print(Path(sys.argv[1]).expanduser().resolve())
PY
  )"
  resolved="${resolved//$'\r'/}"
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -u "${resolved}"
  else
    printf '%s\n' "${resolved}"
  fi
}

install_root_for() {
  local agent="$1"
  local scope="$2"
  local target="$3"

  case "${agent}:${scope}" in
    codex:user|generic:user)
      printf '%s\n' "${HOME}/.agents/skills"
      ;;
    codex:project|generic:project)
      printf '%s\n' "${target}/.agents/skills"
      ;;
    claude:user)
      printf '%s\n' "${HOME}/.claude/skills"
      ;;
    claude:project)
      printf '%s\n' "${target}/.claude/skills"
      ;;
    cursor:user)
      printf '%s\n' "${HOME}/.cursor/skills"
      ;;
    cursor:project)
      printf '%s\n' "${target}/.cursor/skills"
      ;;
    pi:user)
      printf '%s\n' "${HOME}/.pi/agent/skills"
      ;;
    pi:project)
      printf '%s\n' "${target}/.pi/skills"
      ;;
    *)
      echo "Unsupported agent/scope: ${agent}/${scope}" >&2
      exit 2
      ;;
  esac
}

install_path() {
  local source="$1"
  local dest="$2"

  if [[ "${DRY_RUN}" == "1" ]]; then
    echo "Would install: ${source} -> ${dest} (${MODE})"
    return
  fi

  mkdir -p "$(dirname "${dest}")"

  if [[ -e "${dest}" || -L "${dest}" ]]; then
    if [[ "${FORCE}" != "1" ]]; then
      echo "Target exists: ${dest}" >&2
      echo "Use --force to back it up before installing." >&2
      exit 1
    fi
    local stamp backup
    stamp="$(date -u +%Y%m%dT%H%M%SZ)"
    backup="${dest}.backup.${stamp}"
    mv "${dest}" "${backup}"
    echo "Backed up existing target: ${backup}"
  fi

  if [[ "${MODE}" == "symlink" ]]; then
    ln -s "${source}" "${dest}"
  else
    cp -R "${source}" "${dest}"
  fi
  echo "Installed: ${dest}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent)
      AGENT="${2:?Missing value for --agent}"
      shift 2
      ;;
    --target)
      TARGET="${2:?Missing value for --target}"
      shift 2
      ;;
    --scope)
      SCOPE="${2:?Missing value for --scope}"
      shift 2
      ;;
    --mode)
      MODE="${2:?Missing value for --mode}"
      shift 2
      ;;
    --with-rule)
      WITH_RULE=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "${AGENT}" ]]; then
  echo "--agent is required" >&2
  usage >&2
  exit 2
fi

case "${AGENT}" in
  codex|claude|cursor|pi|generic) ;;
  *)
    echo "Unsupported agent: ${AGENT}" >&2
    exit 2
    ;;
esac

case "${SCOPE}" in
  project|user) ;;
  *)
    echo "Unsupported scope: ${SCOPE}" >&2
    exit 2
    ;;
esac

case "${MODE}" in
  copy|symlink) ;;
  *)
    echo "Unsupported mode: ${MODE}" >&2
    exit 2
    ;;
esac

if [[ ! -f "${SOURCE_SKILL}/SKILL.md" ]]; then
  echo "Missing canonical skill source: ${SOURCE_SKILL}/SKILL.md" >&2
  exit 1
fi

TARGET="$(abspath "${TARGET}")"
INSTALL_ROOT="$(install_root_for "${AGENT}" "${SCOPE}" "${TARGET}")"
DEST="${INSTALL_ROOT}/design-craft"

echo "Agent: ${AGENT}"
echo "Scope: ${SCOPE}"
echo "Target: ${TARGET}"
echo "Install root: ${INSTALL_ROOT}"
install_path "${SOURCE_SKILL}" "${DEST}"

if [[ "${AGENT}" == "cursor" && "${WITH_RULE}" == "1" ]]; then
  RULE_SOURCE="${ROOT_DIR}/adapters/cursor/.cursor/rules/design-craft.mdc"
  RULE_DEST="${TARGET}/.cursor/rules/design-craft.mdc"
  install_path "${RULE_SOURCE}" "${RULE_DEST}"
fi

if [[ "${DRY_RUN}" == "1" ]]; then
  echo "dry_run: no files changed"
fi
