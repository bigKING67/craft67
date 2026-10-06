#!/usr/bin/env bash
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_ROOT="${DESIGN_CRAFT_SOURCE_ROOT:-}"
if [[ -z "${SOURCE_ROOT}" && -f "${SKILL_ROOT}/../../upstreams.lock.json" ]]; then
  SOURCE_ROOT="$(cd "${SKILL_ROOT}/../.." && pwd)"
fi
DETECTOR="${DESIGN_CRAFT_IMPECCABLE_DETECTOR:-}"
TARGET="."
JSON_ONLY=0
FULL_JSON=0
DEGRADED=0
DETECTOR_STATUS="available"
DETECTOR_MESSAGE=""
DETECTOR_EXIT_CODE=""

usage() {
  cat <<'EOF'
Usage:
  scripts/design_craft_detect.sh [--target <path>] [--json-only] [--full-json]
  scripts/design_craft_detect.sh <path>

Runs an available Impeccable detector plus portable design-craft signals.

Options:
  --json-only   Emit the raw upstream Impeccable detector JSON for compatibility.
  --full-json   Emit combined upstream and design-craft signal JSON.
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

if [[ -n "${SOURCE_ROOT}" ]]; then
  SOURCE_ROOT="$(abspath "${SOURCE_ROOT}")"
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:?Missing value for --target}"
      shift 2
      ;;
    --json-only)
      JSON_ONLY=1
      shift
      ;;
    --full-json)
      FULL_JSON=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      TARGET="$1"
      shift
      ;;
  esac
done

if [[ -n "${DETECTOR}" ]]; then
  DETECTOR="$(abspath "${DETECTOR}")"
fi

if [[ -z "${DETECTOR}" ]]; then
  detector_candidates=()
  if [[ -n "${SOURCE_ROOT}" ]]; then
    detector_candidates+=("${SOURCE_ROOT}/upstreams/impeccable/skill/scripts/detect.mjs")
  fi
  detector_candidates+=(
    "${HOME}/.agents/skills/impeccable/scripts/detect.mjs"
    "${HOME}/.codex/skills/impeccable/scripts/detect.mjs"
  )
  for candidate in "${detector_candidates[@]}"; do
    if [[ -f "${candidate}" ]]; then
      DETECTOR="${candidate}"
      break
    fi
  done
fi

if [[ -z "${DETECTOR}" || ! -f "${DETECTOR}" ]] || ! command -v node >/dev/null 2>&1; then
  DEGRADED=1
  DETECTOR_STATUS="unavailable"
  DETECTOR_MESSAGE="Impeccable detector or Node runtime is unavailable"
else
  DETECTOR_DIR="$(cd "$(dirname "${DETECTOR}")" && pwd)"
  STATIC_HTML_ENGINE="${DETECTOR_DIR}/../../cli/engine/engines/static-html/detect-html.mjs"
  if [[ -f "${STATIC_HTML_ENGINE}" ]] && ! node --input-type=module --eval '
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const requireFromEngine = createRequire(pathToFileURL(process.argv[1]));
for (const dependency of ["htmlparser2", "css-select", "css-tree", "domutils"]) {
  const resolved = requireFromEngine.resolve(dependency);
  await import(pathToFileURL(resolved).href);
}
' "${STATIC_HTML_ENGINE}" >/dev/null 2>&1; then
    DEGRADED=1
    DETECTOR_STATUS="available_regex_fallback"
    DETECTOR_MESSAGE="optional static HTML/CSS parser dependencies unavailable; source detector is using its regex fallback"
  fi
fi

TARGET="$(abspath "${TARGET}")"
DETECTOR_TARGET="${TARGET}"
DETECTOR_NOTE=""
if [[ -n "${SOURCE_ROOT}" && "${TARGET}" == "${SOURCE_ROOT}" ]]; then
  DETECTOR_TARGET="${SKILL_ROOT}"
  DETECTOR_NOTE="source repo root normalized to installable skill folder"
fi

TMP_JSON="$(mktemp -t design-craft-detect.XXXXXX)"
TMP_STDERR="$(mktemp -t design-craft-detect-stderr.XXXXXX)"
trap 'rm -f "${TMP_JSON}" "${TMP_STDERR}"' EXIT

if [[ "${DETECTOR_STATUS}" != "unavailable" ]]; then
  set +e
  python3 - "$(command -v node)" "${DETECTOR}" "${DETECTOR_TARGET}" "${TMP_JSON}" "${TMP_STDERR}" "${SKILL_ROOT}" <<'PY'
import subprocess
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[6]) / "lib"))
from design_craft.detector_policy import redact_url_userinfo

stdout_limit = 8 * 1024 * 1024
stderr_limit = 1024 * 1024
process = subprocess.Popen(
    [sys.argv[1], sys.argv[2], "--json", sys.argv[3]],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
buffers = {"stdout": bytearray(), "stderr": bytearray()}
overflow = {"stdout": False, "stderr": False}


def drain(name: str, stream, limit: int) -> None:
    while True:
        chunk = stream.read(64 * 1024)
        if not chunk:
            return
        remaining = limit - len(buffers[name])
        if remaining > 0:
            buffers[name].extend(chunk[:remaining])
        if len(chunk) > remaining:
            overflow[name] = True


threads = [
    threading.Thread(target=drain, args=("stdout", process.stdout, stdout_limit)),
    threading.Thread(target=drain, args=("stderr", process.stderr, stderr_limit)),
]
for thread in threads:
    thread.start()
returncode = process.wait()
for thread in threads:
    thread.join()

Path(sys.argv[4]).write_bytes(bytes(buffers["stdout"]))
stderr_text = buffers["stderr"].decode("utf-8", errors="replace")
if overflow["stderr"]:
    stderr_text += "\n[design-craft: detector stderr truncated at 1048576 bytes]\n"
Path(sys.argv[5]).write_text(redact_url_userinfo(stderr_text), encoding="utf-8")
if overflow["stdout"]:
    with Path(sys.argv[5]).open("a", encoding="utf-8") as handle:
        handle.write("design-craft detector: stdout exceeded 8388608 bytes\n")
    raise SystemExit(70)
raise SystemExit(returncode)
PY
  DETECTOR_EXIT_CODE="$?"
  set -e
  if [[ -s "${TMP_STDERR}" ]]; then
    cat "${TMP_STDERR}" >&2
  fi
  if [[ "${DETECTOR_EXIT_CODE}" != "0" && "${DETECTOR_EXIT_CODE}" != "2" ]]; then
    echo "design-craft detector: upstream detector exited ${DETECTOR_EXIT_CODE}" >&2
    exit "${DETECTOR_EXIT_CODE}"
  fi
else
  python3 - "${DETECTOR}" "${DETECTOR_MESSAGE}" <<'PY' >"${TMP_JSON}"
import json
import sys

print(
    json.dumps(
        {
            "status": "unavailable",
            "degraded": True,
            "detector_path": sys.argv[1],
            "issues": [],
            "message": sys.argv[2],
        },
        ensure_ascii=False,
        indent=2,
    )
)
PY
fi

python3 - "${TMP_JSON}" "${SKILL_ROOT}" <<'PY'
import json
import sys
from pathlib import Path

lib_dir = Path(sys.argv[2]) / "lib"
sys.path.insert(0, str(lib_dir))
from design_craft.detector_policy import sanitize_payload

path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
path.write_text(
    json.dumps(sanitize_payload(payload), ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
PY

if [[ "${JSON_ONLY}" == "1" ]]; then
  cat "${TMP_JSON}"
  exit 0
fi

python3 - "${TMP_JSON}" "${TARGET}" "${DETECTOR_TARGET}" "${DETECTOR_NOTE}" "${FULL_JSON}" "${SKILL_ROOT}" "${DETECTOR_STATUS}" "${DEGRADED}" "${DETECTOR}" "${DETECTOR_MESSAGE}" "${DETECTOR_EXIT_CODE}" <<'PY'
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[6]) / "lib"))
from design_craft.authority import asset_root_for, project_root_for, resolve_project_authority
from design_craft.detector_policy import linked_stylesheet_files, sanitize_payload

path = Path(sys.argv[1])
target = sys.argv[2]
detector_target = sys.argv[3]
detector_note = sys.argv[4]
full_json = sys.argv[5] == "1"
skill_root = Path(sys.argv[6])
detector_status = sys.argv[7]
degraded = sys.argv[8] == "1"
detector_path = sys.argv[9]
detector_message = sys.argv[10]
detector_exit_code = int(sys.argv[11]) if sys.argv[11] else None

target_path = Path(target)
scan_root = target_path if target_path.is_dir() else target_path.parent
skip_dirs = {
    ".git",
    ".next",
    ".turbo",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "upstreams",
}
text_suffixes = {".css", ".html", ".js", ".jsx", ".md", ".mdx", ".scss", ".ts", ".tsx"}

try:
    payload = sanitize_payload(json.loads(path.read_text(encoding="utf-8")))
except Exception as exc:
    print(f"design-craft detector: failed to parse JSON for {target}: {exc}", file=sys.stderr)
    raise

if isinstance(payload, list):
    items = payload
elif isinstance(payload, dict):
    items = payload.get("issues") or payload.get("findings") or []
else:
    items = []
upstream_meta = payload if isinstance(payload, dict) else {}

def is_design_craft_self_scan(root: Path) -> bool:
    if (root / "skills/design-craft/SKILL.md").is_file():
        return True
    skill_file = root / "SKILL.md"
    if skill_file.is_file():
        return "name: design-craft" in skill_file.read_text(encoding="utf-8", errors="ignore")
    return False


def iter_text_files(root: Path):
    if root.is_file():
        if root.suffix.lower() in text_suffixes:
            yield root
        return
    for candidate in root.rglob("*"):
        if not candidate.is_file():
            continue
        rel_parts = candidate.relative_to(root).parts
        if any(part in skip_dirs for part in rel_parts):
            continue
        if candidate.suffix.lower() in text_suffixes:
            yield candidate


def read_file(candidate: Path) -> str:
    try:
        if candidate.stat().st_size > 300_000:
            return ""
        return candidate.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def rel(candidate: Path) -> str:
    try:
        return str(candidate.relative_to(scan_root))
    except ValueError:
        return str(candidate)


def finding(rule: str, severity: str, candidate: Path, message: str) -> dict:
    return {
        "source": "design-craft",
        "severity": severity,
        "rule": rule,
        "path": rel(candidate),
        "message": message,
    }


def find_design_authority(root: Path) -> Path | None:
    return resolve_project_authority(root, "DESIGN.md").path


def scan_local_signals(root: Path) -> tuple[list[dict], list[str]]:
    notes: list[str] = []
    signals: list[dict] = []
    if is_design_craft_self_scan(root):
        notes.append("design-craft self scan: local signal rules skipped to avoid self-referential findings")
        return signals, notes

    files = list(iter_text_files(root))
    if root.is_file() and root.suffix.lower() in {".html", ".htm"}:
        stylesheets, stylesheet_issues = linked_stylesheet_files(
            root,
            project_root_for(root),
            asset_root=asset_root_for(root),
        )
        files.extend(stylesheet for stylesheet in stylesheets if stylesheet not in files)
        notes.extend(stylesheet_issues)
    joined_names = " ".join(str(file).lower() for file in files)
    looks_frontend = any(
        marker in joined_names
        for marker in (".tsx", ".jsx", "/src/", "/app/", "package.json", ".css", ".scss")
    ) or (root / "package.json").is_file()

    if looks_frontend and find_design_authority(root) is None:
        signals.append(
            {
                "source": "design-craft",
                "severity": "info",
                "rule": "missing-design-authority",
                "path": ".",
                "message": "No DESIGN.md was found from target upward; route output should document the effective style authority or explain why none exists.",
            }
        )

    for candidate in files:
        text = read_file(candidate)
        if not text:
            continue
        lower = text.lower()

        browser_claim = re.search(r"browser validation[:\s-]*(passed|pass|ok|complete|completed|verified)", lower)
        browser_evidence = (
            "browser validation target" in lower
            or "tmwd_browser" in lower
            or "screenshot" in lower
            or re.search(r"https?://|localhost|127\.0\.0\.1", lower)
        )
        if browser_claim and not browser_evidence:
            signals.append(
                finding(
                    "browser-validation-claim-without-target",
                    "warn",
                    candidate,
                    "Browser validation appears claimed without a target URL, browser tool, or screenshot evidence.",
                )
            )

        generic_card_count = len(re.findall(r"\b(card|cards|grid|bento|gradient|glassmorphism|beautiful|sleek)\b", lower))
        data_terms = len(re.findall(r"\b(data|table|chart|metric|report|dashboard|kpi|query)\b", lower))
        if generic_card_count >= 14 and data_terms <= 3:
            signals.append(
                finding(
                    "generic-card-grid-overuse",
                    "info",
                    candidate,
                    "High generic card/grid language density; verify hierarchy is product-specific rather than templated.",
                )
            )

        if "dashboard" in lower:
            decorative_terms = len(re.findall(r"\b(gradient|glow|blur|shadow|glass|animated|decoration|hero)\b", lower))
            analytical_terms = len(re.findall(r"\b(filter|table|chart|axis|metric|kpi|empty|loading|error|export)\b", lower))
            if decorative_terms >= 8 and analytical_terms <= 4:
                signals.append(
                    finding(
                        "dashboard-decoration-over-content",
                        "info",
                        candidate,
                        "Dashboard language is decoration-heavy; confirm analytical affordances and states are not secondary.",
                    )
                )

        if re.search(r"\btransition\s*:\s*all\b|\btransition-all\b", lower):
            signals.append(
                finding(
                    "motion-transition-all",
                    "info",
                    candidate,
                    "Broad transition-all/all animation detected; verify only intended GPU-friendly properties animate.",
                )
            )

        if re.search(r"\bease-in\b", lower):
            signals.append(
                finding(
                    "motion-ease-in-ui-review",
                    "info",
                    candidate,
                    "ease-in appears in motion code or docs; UI response usually needs ease-out unless context justifies it.",
                )
            )

        if re.search(r"scale\(\s*0(?:\.0+)?\s*\)", lower):
            signals.append(
                finding(
                    "motion-scale-zero-entry",
                    "warn",
                    candidate,
                    "scale(0) entry detected; prefer scale(0.9-0.97) plus opacity for physicality.",
                )
            )

        if re.search(r"transform-origin\s*:\s*center", lower) and re.search(
            r"popover|dropdown|tooltip|menu|select", lower
        ):
            signals.append(
                finding(
                    "motion-origin-aware-review",
                    "info",
                    candidate,
                    "Trigger-anchored popover/dropdown/tooltip with center origin should be reviewed for origin-aware motion.",
                )
            )

        if re.search(r"\b(?:duration|transition(?:-duration)?|animation(?:-duration)?)\s*[:=]\s*[\"']?\d{3,4}ms", lower):
            long_ms = [int(value) for value in re.findall(r"(\d{3,4})ms", lower)]
            if any(value > 300 for value in long_ms):
                signals.append(
                    finding(
                        "motion-ui-duration-review",
                        "info",
                        candidate,
                        "UI motion duration above 300ms appears; verify it is not a frequently-seen interaction.",
                    )
                )

        if re.search(r"(transition|animation)[^;\n]*(width|height|margin|padding|top|left)", lower):
            signals.append(
                finding(
                    "motion-layout-property-animation",
                    "warn",
                    candidate,
                    "Animation or transition touches layout properties; prefer transform/opacity or prove the layout cost is acceptable.",
                )
            )

        if re.search(r":hover|whilehover|while-hover", lower) and re.search(r"transform|scale|translate|rotate", lower):
            if "hover: hover" not in lower and "pointer: fine" not in lower:
                signals.append(
                    finding(
                        "motion-hover-gate-review",
                        "info",
                        candidate,
                        "Hover motion detected without an obvious hover/pointer media gate; verify touch devices do not get sticky hover.",
                    )
                )

        if re.search(r"transition|animation|transform|translate|scale|rotate", lower):
            if "prefers-reduced-motion" not in lower and "usereducedmotion" not in lower:
                signals.append(
                    finding(
                        "motion-reduced-motion-review",
                        "info",
                        candidate,
                        "Movement or transition detected without an obvious reduced-motion path; verify accessibility behavior.",
                    )
                )

        if "report" in lower:
            table_terms = len(re.findall(r"\b(table|row|column|tbody|thead|tr|td)\b", lower))
            chart_terms = len(re.findall(r"\b(chart|figure|visual|summary|insight|takeaway)\b", lower))
            if table_terms >= 12 and chart_terms <= 3:
                signals.append(
                    finding(
                        "report-table-wall-risk",
                        "info",
                        candidate,
                        "Report content appears table-heavy; verify business summary and chart-first hierarchy.",
                    )
                )

        performance_claim = re.search(r"\b(performant|optimized|high performance|性能强|性能优化)\b", lower) or re.search(
            r"\b(fast|faster)\b.{0,48}\b(load|render|page|interaction|query|chart|dashboard)\b|\b(load|render|page|interaction|query|chart|dashboard)\b.{0,48}\b(fast|faster)\b",
            lower,
        )
        measurement_terms = re.search(r"\b(measured|measurement|baseline|lighthouse|web vitals|fps|bundle|profiled|trace)\b", lower)
        if performance_claim and not measurement_terms:
            signals.append(
                finding(
                    "performance-claim-without-measurement",
                    "info",
                    candidate,
                    "Performance is claimed without measurement terms; add baseline/after evidence when this is delivery text.",
                )
            )

        if any(part in {"shared", "common", "utils", "helpers"} for part in candidate.parts):
            signals.append(
                finding(
                    "shared-abstraction-review",
                    "info",
                    candidate,
                    "Shared/helper path detected; confirm at least two real call sites with the same intent before abstraction.",
                )
            )

    return signals, notes


def collect_scanner_signals(root: Path) -> tuple[list[dict], list[str]]:
    scripts = [
        ("css-smell", skill_root / "scripts/design_craft_css_smell_scan.py"),
        ("focus-audit", skill_root / "scripts/design_craft_focus_audit.py"),
        ("token-audit", skill_root / "scripts/design_craft_token_audit.py"),
    ]
    signals: list[dict] = []
    notes: list[str] = []
    if is_design_craft_self_scan(root):
        notes.append("scanner signals skipped for design-craft self scan")
        return signals, notes
    for name, script in scripts:
        if not script.is_file():
            notes.append(f"{name} scanner missing: {script}")
            continue
        try:
            result = subprocess.run(
                [sys.executable, str(script), "--target", str(root), "--json"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=20,
                check=False,
            )
        except Exception as exc:
            notes.append(f"{name} scanner failed to start: {exc}")
            continue
        if result.returncode != 0:
            notes.append(f"{name} scanner exited {result.returncode}: {result.stderr.strip()[:160]}")
            continue
        try:
            payload = json.loads(result.stdout)
        except Exception as exc:
            notes.append(f"{name} scanner emitted invalid JSON: {exc}")
            continue
        for item in payload.get("findings", []):
            if not isinstance(item, dict):
                continue
            signals.append(
                {
                    "source": item.get("source", f"design-craft.{name}"),
                    "severity": item.get("severity", "info"),
                    "rule": item.get("rule", name),
                    "path": item.get("path", "."),
                    "line": item.get("line"),
                    "message": item.get("message", ""),
                }
            )
    return signals, notes


local_signals, local_notes = scan_local_signals(target_path)
scanner_signals, scanner_notes = collect_scanner_signals(target_path)
local_signals.extend(scanner_signals)
local_notes.extend(scanner_notes)

if full_json:
    print(
        json.dumps(
            sanitize_payload({
                "schema": "design-craft.detect.v2",
                "target": target,
                "detector_target": detector_target,
                "detector_note": detector_note,
                "degraded": degraded,
                "upstream_detector": {
                    "status": detector_status,
                    "path": str(upstream_meta.get("detector_path") or detector_path),
                    "message": str(upstream_meta.get("message") or detector_message),
                    "exit_code": detector_exit_code,
                },
                "upstream_findings": items,
                "design_craft_signal_findings": local_signals,
                "design_craft_notes": local_notes,
            }),
            ensure_ascii=False,
            indent=2,
        )
    )
    raise SystemExit(0)

print(f"design-craft detector target: {target}")
if detector_target != target:
    print(f"detector_scan_target: {detector_target}")
if detector_note:
    print(f"detector_note: {detector_note}")
print(f"upstream_detector_findings: {len(items)}")
print(f"upstream_detector_status: {detector_status}")
print(f"degraded: {str(degraded).lower()}")
if detector_message:
    print(f"upstream_detector_message: {detector_message}")
if detector_exit_code is not None:
    print(f"upstream_detector_exit_code: {detector_exit_code}")
print(f"design_craft_signal_findings: {len(local_signals)}")
for note in local_notes:
    print(f"design_craft_note: {note}")

if items:
    severities = Counter(str(item.get("severity", "unknown")) for item in items if isinstance(item, dict))
    if severities:
        print("severity_counts: " + ", ".join(f"{key}={value}" for key, value in sorted(severities.items())))
    print("Treat findings as signals; project DESIGN.md and runtime evidence remain higher authority.")
else:
    print("No upstream detector findings.")

if local_signals:
    local_severities = Counter(str(item.get("severity", "unknown")) for item in local_signals)
    print("design_craft_signal_severity_counts: " + ", ".join(f"{key}={value}" for key, value in sorted(local_severities.items())))
    print("Design-craft signals are review prompts, not automatic failures.")
else:
    print("No design-craft local signal findings.")

print("\nupstream_raw_json:")
PY

if [[ "${FULL_JSON}" != "1" ]]; then
  cat "${TMP_JSON}"
fi
