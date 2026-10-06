#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
printf '%s\n' "warning: scripts/smoke_eval.sh is deprecated; use the complete deterministic gate: scripts/validate.sh." >&2
exec "$ROOT/scripts/validate.sh"
