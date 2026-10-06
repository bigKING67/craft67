#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

TARGET="."
MODE="audit"
SURFACE="auto"
INTENT="auto"
SCOPE="auto"
STYLE="auto"
PLATFORM="auto"
PRODUCT_CONTEXT_PATH=""
SKIP_ROUTE=0
SKIP_DETECTOR=0
SKIP_SCORE=0
STRICT=0

usage() {
  cat <<'EOF'
Usage:
  scripts/design_craft_audit.sh [options]

Options:
  --target <path>     Project, folder, or file to audit.
  --mode <mode>       critique|audit|prototype|system-review|polish|motion|motion-plan|harden|optimize|structure|architecture.
  --surface <value>   Route planner surface, default auto.
  --intent <value>    Route planner intent, default auto.
  --scope <value>     Route planner scope, default auto.
  --style <value>     Route planner style, default auto.
  --platform <value>  auto|web|ios|android|adaptive.
  --product-context-path <path>  Explicit PRODUCT.md.
  --skip-route        Do not call design_craft_route.sh.
  --skip-detector     Do not call design_craft_detect.sh.
  --skip-score        Suppress the repository-quality boundary note.
  --strict            Exit non-zero if a sub-check exits non-zero.
EOF
}

abspath() {
  local resolved
  resolved="$(python3 - "$1" <<'PY'
import sys
from pathlib import Path
print(Path(sys.argv[1]).expanduser().resolve())
PY
  )"
  resolved="${resolved//$'\r'/}"
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -u "${resolved}"
  else
    printf '%s\n' "${resolved}"
  fi
}

section() {
  printf '\n== %s ==\n' "$1"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:?Missing value for --target}"
      shift 2
      ;;
    --mode)
      MODE="${2:?Missing value for --mode}"
      shift 2
      ;;
    --surface)
      SURFACE="${2:?Missing value for --surface}"
      shift 2
      ;;
    --intent)
      INTENT="${2:?Missing value for --intent}"
      shift 2
      ;;
    --scope)
      SCOPE="${2:?Missing value for --scope}"
      shift 2
      ;;
    --style)
      STYLE="${2:?Missing value for --style}"
      shift 2
      ;;
    --platform)
      PLATFORM="${2:?Missing value for --platform}"
      shift 2
      ;;
    --product-context-path)
      PRODUCT_CONTEXT_PATH="$(abspath "${2:?Missing value for --product-context-path}")"
      shift 2
      ;;
    --skip-route)
      SKIP_ROUTE=1
      shift
      ;;
    --skip-detector)
      SKIP_DETECTOR=1
      shift
      ;;
    --skip-score)
      SKIP_SCORE=1
      shift
      ;;
    --strict)
      STRICT=1
      shift
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

case "${MODE}" in
  critique|audit|prototype|system-review|polish|motion|motion-plan|harden|optimize|structure|architecture) ;;
  *)
    echo "Unknown mode: ${MODE}" >&2
    usage >&2
    exit 2
    ;;
esac

TARGET="$(abspath "${TARGET}")"
overall_status=0

section "design-craft ${MODE}"
echo "target: ${TARGET}"
echo "surface: ${SURFACE}"
echo "intent: ${INTENT}"
echo "scope: ${SCOPE}"
echo "style: ${STYLE}"
echo "platform: ${PLATFORM}"
echo "product_context_path: ${PRODUCT_CONTEXT_PATH:-auto}"

if [[ "${SKIP_ROUTE}" != "1" ]]; then
  section "route"
  set +e
  route_cmd=("${ROOT_DIR}/scripts/design_craft_route.sh" \
    --target "${TARGET}" \
    --surface "${SURFACE}" \
    --intent "${INTENT}" \
    --scope "${SCOPE}" \
    --style "${STYLE}" \
    --platform "${PLATFORM}")
  if [[ -n "${PRODUCT_CONTEXT_PATH}" ]]; then
    route_cmd+=(--product-context-path "${PRODUCT_CONTEXT_PATH}")
  fi
  "${route_cmd[@]}"
  status=$?
  set -e
  if [[ "${status}" != "0" ]]; then
    overall_status="${status}"
    echo "route_status: ${status}"
    echo "route_note: inspect preflight output before implementation."
  fi
else
  section "route"
  echo "skipped"
fi

section "platform scan"
platform_cmd=(
  python3 "${ROOT_DIR}/scripts/design_craft_platform_scan.py"
  --target "${TARGET}"
  --platform "${PLATFORM}"
)
if [[ -n "${PRODUCT_CONTEXT_PATH}" ]]; then
  platform_cmd+=(--product-context-path "${PRODUCT_CONTEXT_PATH}")
fi
set +e
"${platform_cmd[@]}"
status=$?
set -e
if [[ "${status}" != "0" ]]; then
  overall_status="${status}"
  echo "platform_scan_status: ${status}"
fi

if [[ "${SKIP_DETECTOR}" != "1" ]]; then
  section "detector"
  set +e
  "${ROOT_DIR}/scripts/design_craft_detect.sh" --target "${TARGET}"
  status=$?
  set -e
  if [[ "${status}" != "0" ]]; then
    overall_status="${status}"
    echo "detector_status: ${status}"
  fi
else
  section "detector"
  echo "skipped"
fi

if [[ "${SKIP_SCORE}" != "1" ]]; then
  section "quality evidence boundary"
  echo "Runtime audit does not compute repository quality scores. Use repo governance tooling for contract, operational, benchmark, evaluation, and certification reports."
else
  section "quality evidence boundary"
  echo "skipped"
fi

section "mode checklist"
case "${MODE}" in
  critique)
    cat <<'EOF'
- Start with one design read: surface, audience, vibe, and primary job.
- Judge product-job fit before decoration: what decision or action becomes clearer?
- Check hierarchy, density, typography rhythm, color intent, motion restraint, and responsive risk.
- Call out generic AI tells: nested-card soup, vague labels, fake gradients, ornamental noise, and weak empty states.
- If the user asks for a score or why the UI is not 100, use product-ui-taste-review.md plus taste-score-calibration.md; label evidence level and product UI taste score.
- Report method provenance for full critiques: dual-agent only if it actually ran; otherwise say single-context/degraded with the reason.
- Classify issues as P0/P1/P2/P3 and recommend the next pass: shape, polish, harden, optimize, or implement.
- Keep this read-only unless the user asks for changes.
EOF
    ;;
  audit)
    cat <<'EOF'
- Confirm authority order: live runtime > scoped AGENTS/README > PRODUCT.md > DESIGN.md > route > design-craft references.
- Classify findings as P0/P1/P2/P3.
- Separate candidate_skills from selected_skills.
- Require browser validation for web UI and native runtime validation for iOS/Android/adaptive UI.
- Require screenshot artifact evidence when route output requires browser screenshots.
- Static native scans cannot be reported as simulator/emulator or hardware verification.
EOF
    ;;
  prototype)
    cat <<'EOF'
- Read references/prototype-workflow.md and narrow the run to one UI piece.
- Record product/style authority, stack, realistic context, required states, and production files excluded from exploration.
- Default to three defensible directions with named product-relevant axes; color, copy, icon, spacing, or decoration-only changes are not separate directions.
- During exploration, write only an isolated prototype surface and local fixtures; do not modify production behavior or shared primitives.
- Render one variant at a time at usable size in the same realistic context; implement decisive interactions, keyboard/focus, themes, and Reduced Motion.
- Do not copy a fixed picker, route, query, CSS, or host wiring when it conflicts with project, framework, or CSP authority.
- Verify runnable variants in the applicable runtime before reporting ready_for_selection; static plans and tests are not rendered evidence.
- Stop before production promotion until the user provides explicit selection or delegated selection; then integrate, run system-consistency closeout, and clean up the prototype by default.
EOF
    ;;
  system-review)
    cat <<'EOF'
- Read references/system-review.md and declare the exact review scope, exclusions, authority, themes, platforms, and evidence baseline.
- Build a surface/route inventory; do not present representative-route evidence as whole-product coverage.
- When an approved reference exists, inventory its salient elements directly before reading a builder summary; classify match, acceptable adaptation, missing, contradicted, or added without approval.
- Build semantic component-family and interaction-pattern inventories with a project exemplar and documented exceptions for each repeated family.
- Review the visual system, visual language, interaction system, and motion system through one unified finding ledger.
- Compare sibling or equivalent controls in the same applicable states; do not force unlike semantic roles into identical styling.
- Complete the component-family x state x theme matrix with verified, not_applicable, unverified, or finding IDs.
- Review visible focus, and conditionally selection, caret, underline offset, tabular numerals, and scrollbar styling when project authority owns those browser-native surfaces.
- Treat screenshot attachment, geometry, default computed styles, scanner output, and automated tests as evidence rather than visual acceptance.
- After fixes, score the original finding IDs resolved, partial, or unresolved from the same decisive evidence; do not restart an unrelated defect hunt.
- Classify findings as P0/P1/P2/P3 and emit exactly one sign-off: pass, blocked, or incomplete. Unresolved P0/P1 blocks delivery.
- Keep this review read-only unless the user separately authorizes implementation.
EOF
    ;;
  polish)
    cat <<'EOF'
- Polish only after function works.
- Check alignment, spacing, hierarchy, line length, tokens, focus, hover, disabled, loading, error, and reduced motion.
- Do not turn polish into redesign without approval.
EOF
    ;;
  motion)
    cat <<'EOF'
- Read references/motion-quality.md before judging animation values.
- Read references/motion-patterns.md when the task needs concrete web component recipes.
- Read references/interaction-physics.md for direct manipulation, momentum, or interruptible gestures.
- Start by asking whether the motion should exist: high-frequency and keyboard-triggered actions usually get no animation.
- Review with a Before | After | Why table; cite file:line when concrete code is available.
- Block feel-breaking motion: ease-in UI response, scale(0), transition-all on hot paths, layout-property animation, missing reduced-motion, or wrong popover origin.
- Check duration bands: press 100-160ms, tooltip/popover 125-200ms, dropdown/select 150-250ms, most UI below 300ms.
- Prefer transform/opacity, CSS/WAAPI for predetermined motion, transitions/springs for interruptible gesture or rapidly-triggered UI.
- Verify presentation-value interruption, velocity handoff, projected endpoints, hysteresis, and reduced-motion alternatives for gesture UI.
- Verdict tiers: feel-breaking regressions, missed simplifications, performance, interruptibility/timing, origin/physicality/cohesion, accessibility.
EOF
    ;;
  motion-plan)
    cat <<'EOF'
- Read references/motion-audit-planning.md, then the relevant sections of motion-quality.md and interaction-physics.md.
- Keep the audit read-only until the user explicitly selects plans for implementation.
- Start with stack, motion locations, local tokens, product personality, interaction frequency, and evidence-level recon.
- Audit purpose/frequency, timing/easing, origin/physicality, interruption, performance, accessibility, cohesion/tokens, and missed opportunities.
- Re-read every cited location; reject duplicates, intentional exceptions, dead code, and unsupported runtime claims.
- Rank by user impact x frequency x confidence / implementation cost and default to the top three to five findings when non-interactive.
- Scaffold one self-contained plan per selected finding with scripts/design_craft_motion_plan.py; include exact files, current excerpts, target behavior, boundaries, validation, feel checks, and drift stop conditions.
- Reconcile plans as proposed, in_progress, complete, stale, or retired; never mark implementation complete from plan existence alone.
EOF
    ;;
  harden)
    cat <<'EOF'
- Test hostile data: empty, long labels, missing fields, 4xx/5xx, slow network, permissions, large numbers, and narrow viewport.
- Bound lists and tables; avoid hidden fallback paths.
- Keep recovery actions visible.
EOF
    ;;
  optimize)
    cat <<'EOF'
- Establish a baseline first.
- Target LCP, INP, CLS, bundle cost, render hot paths, chart/table scale, and animation cost.
- Roll back changes that do not improve the target or simplify code.
EOF
    ;;
  structure)
    cat <<'EOF'
- Add files only where existing conventions support them.
- Shared abstractions require repeated real callers and the same intent.
- Avoid parallel source trees and vague utility folders.
EOF
    ;;
  architecture)
    cat <<'EOF'
- Identify runtime entrypoint, route ownership, state ownership, data sources, trust boundaries, interfaces, migration, and rollback.
- Preserve current architecture unless there is a concrete failure.
EOF
    ;;
esac

section "status"
if [[ "${overall_status}" == "0" ]]; then
  echo "design-craft audit wrapper completed."
else
  echo "design-craft audit wrapper completed with sub-check status ${overall_status}."
fi

if [[ "${STRICT}" == "1" ]]; then
  exit "${overall_status}"
fi

exit 0
