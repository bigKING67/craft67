#!/usr/bin/env bash
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "${SKILL_ROOT}/scripts/design_craft_route_runtime.py" "$@"
