#!/usr/bin/env bash
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_DIR="${SKILL_ROOT}/templates/l4-eval-case"
DEFAULT_OUTPUT_ROOT="${PWD}/evals/product-ui-taste/before-after"

usage() {
  cat <<'USAGE'
Usage:
  design_craft_l4_eval_case.sh --case-id <id> [options]

Create a scaffold for a real L4 product UI taste before/after eval case.

Required:
  --case-id <id>              Filesystem-safe case id, for example generic-review-workbench-local-l4.

Options:
  --surface <text>            Product surface name.
  --primary-user <text>       Primary user/audience.
  --primary-job <text>        Primary job-to-be-done.
  --design-read <text>        One-line design read.
  --output-root <dir>         Directory that will receive <case-id>/.
                              Default: evals/product-ui-taste/before-after.
  --force                     Allow overwriting an existing scaffold directory.
  -h, --help                  Show this help.

The generated case is a scaffold only. Do not count it as L4 until the
screenshot hashes/dimensions, scores, implementation diff, validation commands,
and unverified states are filled with real evidence.
USAGE
}

case_id=""
surface=""
primary_user=""
primary_job=""
design_read=""
output_root="${DEFAULT_OUTPUT_ROOT}"
force=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --case-id)
      case_id="${2:-}"
      shift 2
      ;;
    --surface|--product-surface)
      surface="${2:-}"
      shift 2
      ;;
    --primary-user)
      primary_user="${2:-}"
      shift 2
      ;;
    --primary-job)
      primary_job="${2:-}"
      shift 2
      ;;
    --design-read)
      design_read="${2:-}"
      shift 2
      ;;
    --output-root)
      output_root="${2:-}"
      shift 2
      ;;
    --force)
      force=1
      shift
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

if [[ -z "${case_id}" ]]; then
  echo "Missing required --case-id" >&2
  usage >&2
  exit 2
fi

if [[ ! "${case_id}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
  echo "--case-id must be filesystem-safe and must not contain slashes: ${case_id}" >&2
  exit 2
fi

if [[ ! -d "${TEMPLATE_DIR}" ]]; then
  echo "Missing L4 template directory: ${TEMPLATE_DIR}" >&2
  exit 1
fi

case_dir="${output_root%/}/${case_id}"
if [[ -e "${case_dir}" && "${force}" != "1" ]]; then
  echo "Case directory already exists: ${case_dir}" >&2
  echo "Use --force only when intentionally refreshing an unfinished scaffold." >&2
  exit 1
fi

mkdir -p "${case_dir}"
cp "${TEMPLATE_DIR}/input.md" "${case_dir}/input.md"
cp "${TEMPLATE_DIR}/score.before.json" "${case_dir}/score.before.json"
cp "${TEMPLATE_DIR}/score.after.json" "${case_dir}/score.after.json"
cp "${TEMPLATE_DIR}/diff-summary.md" "${case_dir}/diff-summary.md"
cp "${TEMPLATE_DIR}/validation.md" "${case_dir}/validation.md"

python3 - "${case_dir}" "${case_id}" "${surface}" "${primary_user}" "${primary_job}" "${design_read}" <<'PY'
import json
import sys
from pathlib import Path

case_dir = Path(sys.argv[1])
case_id, surface, primary_user, primary_job, design_read = sys.argv[2:7]

def update_score(path: Path, suffix: str, finding: str) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["case_id"] = f"{case_id}-{suffix}"
    payload["evidence_level"] = "L4"
    payload["maturity_band"] = "TODO"
    payload["required_findings"] = [
        finding,
        "Replace with a real evidence-backed finding",
        "Replace with a real evidence-backed finding",
    ]
    payload["false_positive_guards"] = [
        "Do not count this scaffold as real evidence until screenshot_sha256 and screenshot_dimensions are filled.",
        "Do not claim browser states unless captured in screenshots.json or validation.md.",
        "Do not claim implementation improvement without a linked diff summary.",
    ]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

input_md = f"""# L4 before/after eval: {case_id}

## Context

- Case ID: {case_id}
- Product surface: {surface or "TODO"}
- Primary user: {primary_user or "TODO"}
- Primary job: {primary_job or "TODO"}
- Design read: {design_read or "TODO"}

## Before evidence

| Artifact | Path | SHA-256 | Dimensions |
|---|---|---|---|
| before viewport | TODO | TODO | TODO |

## After evidence

| Artifact | Path | SHA-256 | Dimensions |
|---|---|---|---|
| after viewport | TODO | TODO | TODO |

## Runtime evidence

- Browser target: TODO
- Viewports: TODO
- Interaction states: TODO
- DOM/computed-style evidence: TODO

## Not verified

- TODO
"""
case_dir.joinpath("input.md").write_text(input_md, encoding="utf-8")

update_score(case_dir / "score.before.json", "before", "Replace with a real before finding")
update_score(case_dir / "score.after.json", "after", "Replace with a real after strength or remaining issue")

screenshots = {
    "schema": "design-craft.l4-screenshots.v1",
    "case_id": case_id,
    "route": surface if surface.startswith(("http://", "https://", "/", "file://")) else "TODO",
    "product_surface": surface or "TODO",
    "artifacts": {
        "before": {
            "desktop": {
                "tool": "TODO",
                "target": "viewport",
                "path": "TODO",
                "sha256": "",
                "dimensions": [0, 0],
                "viewport": {"width": 0, "height": 0, "dpr": 0}
            }
        },
        "after": {
            "desktop": {
                "tool": "TODO",
                "target": "viewport",
                "path": "TODO",
                "sha256": "",
                "dimensions": [0, 0],
                "viewport": {"width": 0, "height": 0, "dpr": 0}
            }
        }
    },
    "layout_delta": {},
    "notes": [
        "Fill artifact path, sha256, dimensions, target, viewport, and state for each real screenshot.",
        "Keep screenshot PNGs repo-external; store only metadata here.",
        "Run scripts/design_craft_l4_evidence_manifest.py --validate-screenshots-json screenshots.json --strict after filling real evidence."
    ]
}
case_dir.joinpath("screenshots.json").write_text(
    json.dumps(screenshots, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
PY

echo "created_l4_eval_case=${case_dir}"
echo "next_steps:"
echo "  - Fill screenshot paths, sha256 hashes, and dimensions in input.md and screenshots.json."
echo "  - Fill score.before.json and score.after.json with real scores and findings."
echo "  - Fill diff-summary.md and validation.md with actual changed files and commands."
echo "  - Validate score files with scripts/design_craft_browser_evidence.py --validate-score-json."
echo "  - Validate screenshot manifest with scripts/design_craft_l4_evidence_manifest.py --validate-screenshots-json ${case_dir}/screenshots.json --strict."
