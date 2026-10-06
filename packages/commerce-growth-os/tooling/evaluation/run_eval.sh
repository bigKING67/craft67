#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CASES="${2:-$ROOT/eval/cases.json}"

python3 -B "$ROOT/tooling/evaluation/score_eval.py" --cases "$CASES" --list >/dev/null

if [ "${1:-}" != "" ]; then
  python3 -B "$ROOT/tooling/evaluation/score_eval.py" --cases "$CASES" --answer-dir "$1" --summary
  if [ "$CASES" = "$ROOT/eval/cases.json" ]; then
    python3 -B "$ROOT/tooling/evaluation/lint_answer.py" --answer-dir "$1" --cases "$CASES"
  fi
else
  echo "Eval cases are valid. Provide an answer directory to score saved answers."
fi
