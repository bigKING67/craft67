#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_ROOT="${DESIGN_CRAFT_SKILL_ROOT:-${HOME}/.agents/skills}"
BACKUP_BASE="${DESIGN_CRAFT_BACKUP_ROOT:-${HOME}/.agents/backups}"
KEEP_BACKUPS="${DESIGN_CRAFT_BACKUP_KEEP:-10}"
LOCK_TIMEOUT="${DESIGN_CRAFT_INSTALL_LOCK_TIMEOUT:-30}"
VERIFY_SCRIPT="${ROOT_DIR}/scripts/design_craft_install_verify.py"
DRY_RUN=0
PRUNE_BACKUPS=1
LOCK_DIR="${INSTALL_ROOT}/.design-craft-install.lock"
LOCK_HELD=0
STAGING_PATHS=()

usage() {
  cat <<'EOF'
Usage:
  scripts/install_local.sh [--dry-run]
                           [--keep-backups <count>] [--no-prune-backups]
                           [--lock-timeout <seconds>]

Installs through a same-filesystem staging directory, validates the staged
copy, atomically replaces the target, and restores the previous target if
post-install verification fails.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --keep-backups)
      KEEP_BACKUPS="${2:?Missing value for --keep-backups}"
      shift 2
      ;;
    --no-prune-backups)
      PRUNE_BACKUPS=0
      shift
      ;;
    --lock-timeout)
      LOCK_TIMEOUT="${2:?Missing value for --lock-timeout}"
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

if [[ ! "${KEEP_BACKUPS}" =~ ^[0-9]+$ ]]; then
  echo "--keep-backups must be a non-negative integer" >&2
  exit 2
fi
if [[ ! "${LOCK_TIMEOUT}" =~ ^[0-9]+$ ]]; then
  echo "--lock-timeout must be a non-negative integer" >&2
  exit 2
fi
if [[ ! -x "${VERIFY_SCRIPT}" ]]; then
  echo "Missing executable install verifier: ${VERIFY_SCRIPT}" >&2
  exit 1
fi

cleanup() {
  local path
  for path in "${STAGING_PATHS[@]:-}"; do
    if [[ -n "${path}" && -d "${path}" ]]; then
      rm -rf "${path}"
    fi
  done
  if [[ "${LOCK_HELD}" == "1" && -d "${LOCK_DIR}" ]]; then
    rm -rf "${LOCK_DIR}"
  fi
}
trap cleanup EXIT INT TERM

acquire_lock() {
  mkdir -p "${INSTALL_ROOT}"
  local waited=0
  while ! mkdir "${LOCK_DIR}" 2>/dev/null; do
    local owner=""
    if [[ -f "${LOCK_DIR}/pid" ]]; then
      owner="$(sed -n '1p' "${LOCK_DIR}/pid" 2>/dev/null || true)"
    fi
    if [[ "${owner}" =~ ^[0-9]+$ ]] && ! kill -0 "${owner}" 2>/dev/null; then
      rm -rf "${LOCK_DIR}"
      continue
    fi
    if (( waited >= LOCK_TIMEOUT )); then
      echo "Timed out waiting for install lock: ${LOCK_DIR}" >&2
      exit 1
    fi
    sleep 1
    waited=$((waited + 1))
  done
  printf '%s\n' "$$" > "${LOCK_DIR}/pid"
  LOCK_HELD=1
}

write_metadata() {
  local target="$1"
  local name="$2"
  local version="$3"
  local commit="unavailable"
  local repo="unavailable"
  local repo_dirty="true"
  local skill_source_dirty="true"

  commit="$(git -C "${ROOT_DIR}" rev-parse HEAD 2>/dev/null || printf '%s' 'unavailable')"
  repo="$(git -C "${ROOT_DIR}" remote get-url origin 2>/dev/null || printf '%s' 'unavailable')"
  if [[ "${commit}" != "unavailable" ]]; then
    if [[ -z "$(git -C "${ROOT_DIR}" status --porcelain=v1 --untracked-files=all 2>/dev/null || true)" ]]; then
      repo_dirty="false"
    fi
    if [[ -z "$(git -C "${ROOT_DIR}" status --porcelain=v1 --untracked-files=all -- "skills/${name}" 2>/dev/null || true)" ]]; then
      skill_source_dirty="false"
    fi
  fi

  python3 - "${target}" "${name}" "${version}" "${ROOT_DIR}" "${commit}" "${repo}" "${repo_dirty}" "${skill_source_dirty}" <<'PY'
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

target, name, version, source_root, commit, repo, repo_dirty, skill_source_dirty = sys.argv[1:]
if "://" in repo:
    parsed = urlsplit(repo)
    host = parsed.hostname or ""
    if parsed.port:
        host = f"{host}:{parsed.port}"
    repo = urlunsplit((parsed.scheme, host, parsed.path, "", ""))
target_path = Path(target)
source_root_path = Path(source_root)
sys.path.insert(0, str(source_root_path / "scripts"))

from design_craft_evidence_common import tree_sha256


def release_state() -> str:
    changelog_path = source_root_path / "CHANGELOG.md"
    if not changelog_path.is_file():
        return "unknown"
    changelog = changelog_path.read_text(encoding="utf-8")
    match = re.search(rf"^## {re.escape(version)} - (?P<label>[^\n]+)$", changelog, flags=re.M)
    if not match:
        return "unknown"
    label = match.group("label").strip()
    if label == "Unreleased":
        return "development"
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", label):
        return "unknown"
    tag_result = subprocess.run(
        ["git", "-C", str(source_root_path), "rev-list", "-n", "1", f"v{version}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    return "released" if tag_result.stdout.strip() == commit else "release_candidate"


payload = {
    "schema": "design-craft.install.v2",
    "installer_version": 3,
    "skill_name": name,
    "version": version,
    "release_state": release_state(),
    "source_root": source_root,
    "source_path": str(Path(source_root) / "skills" / name),
    "source_repo": repo,
    "source_commit": commit,
    "source_dirty": skill_source_dirty == "true",
    "skill_source_dirty": skill_source_dirty == "true",
    "repo_dirty": repo_dirty == "true",
    "source_tree_sha256": tree_sha256(target_path),
    "installed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}
target_path.joinpath(".design-craft-install.json").write_text(
    json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
PY
}

clean_runtime_artifacts() {
  python3 - "$1" <<'PY'
import shutil
import sys
from pathlib import Path

target = Path(sys.argv[1])
for cache_dir in target.rglob("__pycache__"):
    if cache_dir.is_dir():
        shutil.rmtree(cache_dir)
for bytecode in target.rglob("*.py[co]"):
    if bytecode.is_file():
        bytecode.unlink()
for ds_store in target.rglob(".DS_Store"):
    if ds_store.is_file():
        ds_store.unlink()
PY
}

prune_backups() {
  local backup_root="$1"
  if [[ "${PRUNE_BACKUPS}" != "1" || ! -d "${backup_root}" ]]; then
    return
  fi
  python3 - "${backup_root}" "${KEEP_BACKUPS}" <<'PY'
import re
import shutil
import sys
from pathlib import Path

root = Path(sys.argv[1])
keep = int(sys.argv[2])
pattern = re.compile(r"^(?:failed-)?(\d{8}T\d{6}Z(?:-\d+-\d+)?)$")
candidates = []
for path in root.iterdir():
    match = pattern.fullmatch(path.name) if path.is_dir() else None
    if match:
        candidates.append((match.group(1), path))
candidates.sort(key=lambda item: item[0], reverse=True)
for _, path in candidates[keep:]:
    shutil.rmtree(path)
PY
}

verify_install() {
  local source="$1"
  local target="$2"
  local name="$3"
  local version="$4"
  python3 "${VERIFY_SCRIPT}" \
    --source "${source}" \
    --installed "${target}" \
    --expected-name "${name}" \
    --expected-version "${version}" \
    --require-metadata
}

install_one() {
  local name="$1"
  local source="${ROOT_DIR}/skills/${name}"
  local target="${INSTALL_ROOT}/${name}"
  local backup_root="${BACKUP_BASE}/${name}"
  local version
  version="$(tr -d '[:space:]' < "${ROOT_DIR}/VERSION")"

  if [[ ! -f "${source}/SKILL.md" ]]; then
    echo "Missing skill source: ${source}/SKILL.md" >&2
    exit 1
  fi

  echo "Source: ${source}"
  echo "Target: ${target}"

  if [[ "${DRY_RUN}" == "1" ]]; then
    if [[ -e "${target}" || -L "${target}" ]]; then
      echo "Would backup existing ${name} target under: ${backup_root}"
    fi
    echo "Would stage, verify, and atomically install ${name}."
    return
  fi

  local stage
  stage="$(mktemp -d "${INSTALL_ROOT}/.${name}.staging.XXXXXX")"
  STAGING_PATHS+=("${stage}")
  cp -R "${source}/." "${stage}/"
  clean_runtime_artifacts "${stage}"
  write_metadata "${stage}" "${name}" "${version}"
  verify_install "${source}" "${stage}" "${name}" "${version}" >/dev/null

  local backup=""
  local stamp
  stamp="$(date -u +%Y%m%dT%H%M%SZ)-$$-${RANDOM}"
  if [[ -e "${target}" || -L "${target}" ]]; then
    mkdir -p "${backup_root}"
    backup="${backup_root}/${stamp}"
    mv "${target}" "${backup}"
    echo "Backed up existing ${name} skill to: ${backup}"
  fi

  if [[ "${DESIGN_CRAFT_INSTALL_TEST_FAIL_AFTER_BACKUP:-0}" == "1" ]]; then
    if [[ -n "${backup}" && -e "${backup}" ]]; then
      mv "${backup}" "${target}"
    fi
    echo "Injected test failure after backup; previous ${name} target was restored." >&2
    exit 97
  fi

  if ! mv "${stage}" "${target}"; then
    if [[ -n "${backup}" && -e "${backup}" ]]; then
      mv "${backup}" "${target}"
    fi
    echo "Atomic install failed; previous ${name} target was restored." >&2
    exit 1
  fi

  if [[ "${DESIGN_CRAFT_INSTALL_TEST_FAIL_AFTER_SWITCH:-0}" == "1" ]] || ! verify_install "${source}" "${target}" "${name}" "${version}" >/dev/null; then
    mkdir -p "${backup_root}"
    mv "${target}" "${backup_root}/failed-${stamp}"
    if [[ -n "${backup}" && -e "${backup}" ]]; then
      mv "${backup}" "${target}"
    fi
    prune_backups "${backup_root}"
    echo "Post-install verification failed; previous ${name} target was restored." >&2
    exit 1
  fi

  prune_backups "${backup_root}"
  echo "Installed ${name} skill to: ${target}"
}

if [[ "${DRY_RUN}" != "1" ]]; then
  acquire_lock
fi

install_one "design-craft"

if [[ "${DRY_RUN}" == "1" ]]; then
  echo "dry_run: no files changed"
fi
