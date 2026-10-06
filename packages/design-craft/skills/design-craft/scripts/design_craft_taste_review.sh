#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

TARGET="."
CONTEXT=""
EVIDENCE_LEVEL="L0"
OUTPUT=""
PLATFORM="auto"

usage() {
  cat <<'EOF'
Usage:
  scripts/design_craft_taste_review.sh [options]

Options:
  --target <path>          Screenshot, project, folder, or file to review.
  --context <text>         Product context or user brief.
  --evidence-level <L0-L4> Evidence depth. Default: L0.
  --output <path>          Write the review packet to a file instead of stdout.
  --platform <value>       auto|web|ios|android|adaptive. Default: auto.

This wrapper does not judge the UI by itself. It creates a stable product UI
taste-review packet so an agent uses the same score contract, evidence labels,
references, and acceptance criteria every time.
EOF
}

abspath_if_local() {
  python3 - "$1" <<'PY'
import sys
from pathlib import Path

raw = sys.argv[1]
path = Path(raw).expanduser()
if path.exists():
    print(path.resolve())
else:
    print(raw)
PY
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:?Missing value for --target}"
      shift 2
      ;;
    --context)
      CONTEXT="${2:?Missing value for --context}"
      shift 2
      ;;
    --evidence-level)
      EVIDENCE_LEVEL="${2:?Missing value for --evidence-level}"
      shift 2
      ;;
    --output)
      OUTPUT="${2:?Missing value for --output}"
      shift 2
      ;;
    --platform)
      PLATFORM="${2:?Missing value for --platform}"
      shift 2
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

case "${EVIDENCE_LEVEL}" in
  L0|L1|L2|L3|L4) ;;
  *)
    echo "Unknown evidence level: ${EVIDENCE_LEVEL}" >&2
    usage >&2
    exit 2
    ;;
esac

case "${PLATFORM}" in
  auto|web|ios|android|adaptive) ;;
  *)
    echo "Unknown platform: ${PLATFORM}" >&2
    exit 2
    ;;
esac

TARGET="$(abspath_if_local "${TARGET}")"

case "${EVIDENCE_LEVEL}" in
  L0)
    EVIDENCE_LABEL="static screenshot or static description only"
    ;;
  L1)
    EVIDENCE_LABEL="static screenshot plus product context"
    ;;
  L2)
    EVIDENCE_LABEL="observed runtime screenshot plus DOM/computed-style or native source/state evidence"
    ;;
  L3)
    EVIDENCE_LABEL="browser evidence plus responsive and interaction states"
    ;;
  L4)
    EVIDENCE_LABEL="before/after evidence plus measurable validation"
    ;;
esac

emit_packet() {
  cat <<EOF
# Product UI Taste Review Packet

Method: DEGRADED: single-context (packet generated locally; claim dual-agent,
browser, DOM, detector, or responsive evidence only if those steps actually run)

Target: ${TARGET}
Platform: ${PLATFORM}
Evidence level: ${EVIDENCE_LEVEL} - ${EVIDENCE_LABEL}
Context: ${CONTEXT:-not provided}

## Required references

- ${ROOT_DIR}/references/product-ui-taste-review.md
- ${ROOT_DIR}/references/taste-score-calibration.md
- ${ROOT_DIR}/references/product-context.md
- ${ROOT_DIR}/references/product-design-principles.md
- ${ROOT_DIR}/references/visual-judgment.md when the surface needs
  stronger visual anti-slop review.
- ${ROOT_DIR}/references/design-system-contract.md when tokens,
  component states, or theme parity matter.
- Read the matching iOS/Android/adaptive reference when the resolved platform
  is native.
- Project PRODUCT.md, DESIGN.md, scoped AGENTS.md, and live runtime evidence still
  outrank generic taste guidance.

## Evidence contract

- State the evidence level before the score.
- State the platform and whether it was explicit, from PRODUCT.md, inferred, or
  defaulted.
- Do not score hover, focus, loading, error, empty, keyboard, mobile, or
  long-content behavior as verified unless those states were actually checked.
- Separate a static product UI taste score from the design-craft source score.
- Keep score confidence lower for ${EVIDENCE_LEVEL} unless the missing evidence
  is irrelevant to the question.

## Required output

Use this shape for a full review:

1. Overall Score: "__ / 100" plus maturity band.
2. One-Sentence Diagnosis.
3. Design Direction.
4. Top Issues table with Priority, Location, Category, Problem,
   Why It Hurts Taste, Recommendation, and Acceptance Criteria.
5. Detailed Review across the product-ui-taste dimensions, compressed when the
   target is small.
6. Redesign Recommendation.
7. Concrete Before / After Suggestions.
8. Frontend Implementation Notes with tokens, components, layout primitives,
   CSS smells, responsive behavior, and state variants.
9. Acceptance Checklist.

## Calibration guardrails

- 75-84 usually means clean but generic: usable and aligned, but weak product
  judgment, flat hierarchy, card soup, generic surfaces, or underdefined states.
- 85-92 means polished and professional: strong hierarchy and system discipline,
  but not yet exceptional under real content and state coverage.
- 93-97 requires refined product judgment, real-content resilience, responsive
  proof, accessible states, and coherent implementation.
- 98-100 requires exceptional system-level quality. Do not assign it from a
  static screenshot alone.
EOF
}

if [[ -n "${OUTPUT}" ]]; then
  mkdir -p "$(dirname "${OUTPUT}")"
  emit_packet >"${OUTPUT}"
  echo "wrote taste review packet: ${OUTPUT}"
else
  emit_packet
fi
