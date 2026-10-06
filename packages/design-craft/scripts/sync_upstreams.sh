#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME=""
COMMIT=""

usage() {
  cat <<'EOF'
Usage:
  scripts/sync_upstreams.sh --name <taste-skill|impeccable|emilkowalski-skills|jakubkrehel-skills> --commit <sha>

Fetches and checks out one explicit upstream commit, then updates only the
compatibility `commit` field in upstreams.lock.json. Review metadata and
`reviewed_through_commit`, `behavior_absorbed_through_commit`, `latest_range_*`,
and their legacy aliases are intentionally never advanced automatically.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)
      NAME="${2:?Missing value for --name}"
      shift 2
      ;;
    --commit)
      COMMIT="${2:?Missing value for --commit}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "${NAME}" in
  taste-skill|impeccable|emilkowalski-skills|jakubkrehel-skills) ;;
  *)
    echo "--name must be taste-skill, impeccable, emilkowalski-skills, or jakubkrehel-skills" >&2
    exit 2
    ;;
esac

if [[ ! "${COMMIT}" =~ ^[0-9a-fA-F]{40}$ ]]; then
  echo "--commit must be a full 40-character Git SHA" >&2
  exit 2
fi

cd "${ROOT_DIR}"
path="upstreams/${NAME}"
before="$(git -C "${path}" rev-parse HEAD 2>/dev/null || true)"

git -C "${path}" fetch origin "${COMMIT}"
git -C "${path}" checkout --detach "${COMMIT}"

python3 - "${NAME}" "${COMMIT}" <<'PY'
import json
import sys
from pathlib import Path

name, commit = sys.argv[1:]
path = Path("upstreams.lock.json")
payload = json.loads(path.read_text(encoding="utf-8"))
upstreams = payload.get("upstreams", {})
if name not in upstreams:
    raise SystemExit(f"upstream missing from lock: {name}")
upstreams[name]["commit"] = commit
path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY

echo "${NAME}: ${before:-none} -> ${COMMIT}"
echo "Updated only the pinned upstreams.lock.json commit. Review and set remote/absorbed metadata manually."
