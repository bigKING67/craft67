#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_skill="${repo_root}/skills/3d-craft"
destination_root="${AGENTS_SKILLS_ROOT:-${HOME}/.agents/skills}"
destination="${destination_root}/3d-craft"

mkdir -p "${destination_root}"
stage_root="$(mktemp -d "${destination_root}/.3d-craft-stage.XXXXXX")"
backup_root="${destination_root}/.3d-craft-backups"
backup_path=""
cleanup() { rm -rf "${stage_root}"; }
trap cleanup EXIT

cp -R "${source_skill}" "${stage_root}/3d-craft"
python3 "${repo_root}/scripts/validate_source.py" --skill-root "${stage_root}/3d-craft"

if [[ -e "${destination}" ]]; then
  mkdir -p "${backup_root}"
  backup_path="${backup_root}/3d-craft.$(date -u +%Y%m%dT%H%M%SZ)"
  mv "${destination}" "${backup_path}"
fi

if ! mv "${stage_root}/3d-craft" "${destination}"; then
  if [[ -n "${backup_path}" && -e "${backup_path}" ]]; then
    mv "${backup_path}" "${destination}"
  fi
  exit 2
fi

if ! python3 "${repo_root}/scripts/validate_source.py" --skill-root "${destination}"; then
  failed_path="${destination_root}/.3d-craft-failed.$(date -u +%Y%m%dT%H%M%SZ)"
  mv "${destination}" "${failed_path}"
  if [[ -n "${backup_path}" && -e "${backup_path}" ]]; then
    mv "${backup_path}" "${destination}"
  fi
  echo "Install verification failed; candidate retained at ${failed_path}" >&2
  exit 2
fi

digest="$(
  cd "${destination}"
  find . -type f -print0 | sort -z | xargs -0 shasum -a 256 | shasum -a 256 | awk '{print $1}'
)"
printf 'Installed 3d-craft 0.1.0\npath=%s\nprovenance_sha256=%s\n' "${destination}" "${digest}"
if [[ -n "${backup_path}" ]]; then
  printf 'backup=%s\n' "${backup_path}"
fi
