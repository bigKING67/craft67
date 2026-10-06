#!/usr/bin/env bash
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_DIR="${SKILL_ROOT}/templates/developer-product"

TARGET="."
FORCE=0
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage:
  scripts/design_craft_seed_design.sh [options]

Options:
  --target <project-dir>  Project directory that should receive DESIGN.md files.
  --force                 Overwrite existing DESIGN.md / DESIGN.dark.md.
  --dry-run               Print planned writes without changing files.

Copies the original design-craft developer-product seed templates to:
  <project-dir>/DESIGN.md
  <project-dir>/DESIGN.dark.md
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

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:?Missing value for --target}"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
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

TARGET="$(abspath "${TARGET}")"
LIGHT_TEMPLATE="${TEMPLATE_DIR}/design.md"
DARK_TEMPLATE="${TEMPLATE_DIR}/design.dark.md"
LIGHT_TARGET="${TARGET}/DESIGN.md"
DARK_TARGET="${TARGET}/DESIGN.dark.md"

if [[ ! -d "${TARGET}" ]]; then
  echo "Target must be an existing project directory: ${TARGET}" >&2
  exit 1
fi

for template in "${LIGHT_TEMPLATE}" "${DARK_TEMPLATE}"; do
  if [[ ! -f "${template}" ]]; then
    echo "Missing bundled template: ${template}" >&2
    exit 1
  fi
done

conflicts=()
for path in "${LIGHT_TARGET}" "${DARK_TARGET}"; do
  if [[ -e "${path}" && "${FORCE}" != "1" ]]; then
    conflicts+=("${path}")
  fi
done

if (( ${#conflicts[@]} > 0 )); then
  echo "Refusing to overwrite existing design authority files:" >&2
  for path in "${conflicts[@]}"; do
    echo "  - ${path}" >&2
  done
  echo "Use --force only when replacing these files is intentional." >&2
  exit 1
fi

write_template() {
  local source="$1"
  local dest="$2"
  if [[ "${DRY_RUN}" == "1" ]]; then
    printf 'would copy %s -> %s\n' "${source}" "${dest}"
  else
    cp "${source}" "${dest}"
    printf 'copied %s -> %s\n' "${source}" "${dest}"
  fi
}

write_template "${LIGHT_TEMPLATE}" "${LIGHT_TARGET}"
write_template "${DARK_TEMPLATE}" "${DARK_TARGET}"

if [[ "${DRY_RUN}" == "1" ]]; then
  echo "dry_run: no files changed"
else
  echo "seeded design-craft developer-product DESIGN.md pair"
fi
