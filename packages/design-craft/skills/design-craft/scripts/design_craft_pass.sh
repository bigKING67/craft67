#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Usage:
  scripts/design_craft_pass.sh [design_craft_audit.sh options]

Preferred neutral wrapper for design-craft quality passes.

Examples:
  scripts/design_craft_pass.sh --target /path/to/project --mode critique
  scripts/design_craft_pass.sh --target /path/to/project --mode harden

Supported modes are delegated to design_craft_audit.sh:
  critique|audit|prototype|system-review|polish|motion|motion-plan|harden|optimize|structure|architecture
EOF
  exit 0
fi

exec "${ROOT_DIR}/scripts/design_craft_audit.sh" "$@"
