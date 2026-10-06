#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
QUALITY_EVIDENCE="${1:-}"

if [[ -z "$QUALITY_EVIDENCE" ]]; then
  printf '%s\n' "usage: scripts/build_release.sh /path/to/passing-quality-regression.json" >&2
  exit 2
fi

TEMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/commerce-growth-release.XXXXXX")"
trap 'rm -rf "$TEMP_ROOT"' EXIT

bash "$ROOT/scripts/validate.sh"
python3 -B "$ROOT/tooling/validation/check_release.py"
bash "$ROOT/scripts/install.sh" --install-root "$TEMP_ROOT/installed"
python3 -B "$ROOT/tooling/installation/verify_install.py" --install-root "$TEMP_ROOT/installed"
python3 -B "$ROOT/tooling/build/package_release.py" \
  --install-root "$TEMP_ROOT/installed" \
  --quality-evidence "$QUALITY_EVIDENCE" \
  --output-dir "$ROOT/dist"
VERSION="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["pack_version"])' "$ROOT/skill-pack.json")"
python3 -B "$ROOT/tooling/build/verify_release.py" "$ROOT/dist/v$VERSION"
