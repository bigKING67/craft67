#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_DIR="${ROOT_DIR}/skills/design-craft"
EXTERNAL_VALIDATOR="${SKILL_CREATOR_QUICK_VALIDATE:-}"
PORTABLE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --portable)
      PORTABLE=1
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: $0 [--portable]" >&2
      exit 2
      ;;
  esac
  shift
done

cd "${ROOT_DIR}"
export PYTHONDONTWRITEBYTECODE=1

if [[ -z "${DESIGN_CRAFT_BASH:-}" ]]; then
  if command -v cygpath >/dev/null 2>&1; then
    DESIGN_CRAFT_BASH="$(cygpath -w "${BASH}")"
  else
    DESIGN_CRAFT_BASH="${BASH}"
  fi
fi
export DESIGN_CRAFT_BASH

if [[ "${PORTABLE}" == "0" && -n "${EXTERNAL_VALIDATOR}" ]]; then
  if [[ ! -f "${EXTERNAL_VALIDATOR}" ]]; then
    echo "Missing external skill validator: ${EXTERNAL_VALIDATOR}" >&2
    echo "Set SKILL_CREATOR_QUICK_VALIDATE to a compatible quick_validate.py path." >&2
    exit 1
  fi
  python3 -m tools.design_craft.validation.skill_schema --check "${SKILL_DIR}"
  python3 "${EXTERNAL_VALIDATOR}" "${SKILL_DIR}"
fi

exec python3 -m tools.design_craft validate --profile portable
