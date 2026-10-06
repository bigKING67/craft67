#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${PWD}"
JSON=0

usage() {
  cat <<'EOF'
Usage:
  scripts/design_craft_doctor.sh [--target <path>] [--json]

Checks portable design-craft prerequisites without modifying files.
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

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:?Missing value for --target}"
      shift 2
      ;;
    --json)
      JSON=1
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

TARGET="$(abspath "${TARGET}")"

python3 - "${ROOT_DIR}" "${TARGET}" "${JSON}" <<'PY'
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
target = Path(sys.argv[2])
emit_json = sys.argv[3] == "1"
home = Path.home()

def check(name: str, ok: bool, detail: str, *, required: bool = True) -> dict:
    return {"name": name, "ok": bool(ok), "required": required, "detail": detail}

def run_json(command: list[str]) -> tuple[dict, str]:
    result = subprocess.run(
        command,
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {}
    detail = "; ".join(payload.get("errors", [])) or result.stderr.strip()
    return payload, detail

route_plan = Path(os.environ.get("DESIGN_CRAFT_ROUTE_PLAN", str(home / ".codex/tools/frontend_route_plan.sh")))
quick_validate = Path(os.environ.get("SKILL_CREATOR_QUICK_VALIDATE", str(root / "tools/design_craft/validation/skill_schema.py")))
codex_home = Path(os.environ.get("CODEX_HOME", str(home / ".codex")))
version = (root / "VERSION").read_text(encoding="utf-8").strip()
skill_version = (root / "skills/design-craft/VERSION").read_text(encoding="utf-8").strip() if (root / "skills/design-craft/VERSION").is_file() else ""
try:
    compatibility = json.loads((root / "skills/design-craft/COMPATIBILITY.json").read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    compatibility = {}
expected_route_schema = compatibility.get("codex_route_pack", {}).get("schema")
expected_manifest_schema = compatibility.get("codex_route_pack", {}).get("manifest_schema")
expected_snapshot_schema = compatibility.get("codex_route_pack", {}).get("snapshot_schema")
route_payload: dict = {}
route_detail = "route pack unavailable"
if (root / "scripts/design_craft_codex_route_pack.py").is_file():
    route_payload, route_detail = run_json([
        sys.executable,
        "scripts/design_craft_codex_route_pack.py",
        "--strict",
        "--json",
    ])
route_pack_manifest = route_payload.get("route_pack_manifest", {})
route_pack_manifest_ok = route_pack_manifest.get("status") == "ok"
route_pack_missing = route_payload.get("summary", {}).get("missing_required", [])
if not isinstance(route_pack_missing, list):
    route_pack_missing = []
manifest_errors = route_pack_manifest.get("errors", [])
if isinstance(manifest_errors, list) and manifest_errors:
    route_detail = "; ".join(str(item) for item in manifest_errors)
semantic_issues = route_payload.get("semantic_validation", {}).get("issues", [])
if not route_detail and isinstance(semantic_issues, list) and semantic_issues:
    route_detail = "; ".join(str(item) for item in semantic_issues)
semantic_payload = route_payload.get("semantic_validation", {})
runtime_probes = semantic_payload.get("runtime_probes", [])
if not isinstance(runtime_probes, list):
    runtime_probes = []
runtime_probe_map = {
    str(item.get("name")): item
    for item in runtime_probes
    if isinstance(item, dict) and item.get("name")
}
route_modules = semantic_payload.get("route_modules", [])
required_route_modules = {
    "frontend_route_core.py",
    "frontend_route_authority.py",
    "frontend_route_browser.py",
    "frontend_route_delivery.py",
    "frontend_route_runtime.py",
    "frontend_route_telemetry.py",
}
route_modules_ok = isinstance(route_modules, list) and required_route_modules.issubset(route_modules)
route_runtime_truth_ok = runtime_probe_map.get("verified_environment_runtime_profile", {}).get("ok") is True
route_telemetry_ok = runtime_probe_map.get("route_telemetry_self_check", {}).get("ok") is True
route_compatible = (
    expected_route_schema == "design-craft.codex-route-pack.v2"
    and expected_manifest_schema == "codex.frontend-route-pack.manifest.v1"
    and expected_snapshot_schema == "codex.global_agents.snapshot.v2"
    and route_payload.get("schema") == expected_route_schema
    and route_pack_manifest.get("schema") == expected_manifest_schema
    and route_payload.get("status") == "ok"
)

install_root = Path(os.environ.get("DESIGN_CRAFT_SKILL_ROOT", str(home / ".agents/skills"))).expanduser()
install_verifier = root / "scripts/design_craft_install_verify.py"

def installed_check(name: str, source: Path) -> dict:
    installed = install_root / name
    if not installed.is_dir():
        return check(f"installed {name}", True, f"not installed (optional): {installed}", required=False)
    payload, detail = run_json([
        sys.executable,
        str(install_verifier),
        "--source",
        str(source),
        "--installed",
        str(installed),
        "--expected-name",
        name,
        "--expected-version",
        version,
        "--require-metadata",
        "--json",
    ])
    return check(f"installed {name}", payload.get("ok") is True, detail or str(installed), required=False)

checks = [
    check("canonical skill", (root / "skills/design-craft/SKILL.md").is_file(), str(root / "skills/design-craft/SKILL.md")),
    check("codex adapter", (root / "adapters/codex/README.md").is_file(), str(root / "adapters/codex/README.md")),
    check("codex route-pack docs", (root / "adapters/codex/route-pack/README.md").is_file(), str(root / "adapters/codex/route-pack/README.md")),
    check("cursor adapter", (root / "adapters/cursor/README.md").is_file(), str(root / "adapters/cursor/README.md")),
    check("claude adapter", (root / "adapters/claude/README.md").is_file(), str(root / "adapters/claude/README.md")),
    check("pi adapter", (root / "adapters/pi/README.md").is_file(), str(root / "adapters/pi/README.md")),
    check("generic adapter", (root / "adapters/generic/README.md").is_file(), str(root / "adapters/generic/README.md")),
    check("route planner", route_plan.is_file(), str(route_plan), required=False),
    check("codex route pack helper", (root / "scripts/design_craft_codex_route_pack.py").is_file(), str(root / "scripts/design_craft_codex_route_pack.py")),
    check("codex route pack manifest", route_pack_manifest_ok, route_detail or str(codex_home / "tools/frontend_route_pack_manifest.json"), required=False),
    check("codex route pack required files", route_pack_manifest_ok and not route_pack_missing, ", ".join(route_pack_missing) if route_pack_missing else str(codex_home), required=False),
    check("codex route pack compatibility", route_compatible, route_detail or f"{route_payload.get('schema')} == {expected_route_schema}", required=False),
    check("codex route module split", route_modules_ok, ", ".join(sorted(required_route_modules)), required=False),
    check("codex route runtime truth", route_runtime_truth_ok, "verified explicit environment evidence without session discovery", required=False),
    check("codex route telemetry", route_telemetry_ok, "privacy-safe telemetry self-check under an inherited test context", required=False),
    check("skill schema validator", quick_validate.is_file(), str(quick_validate)),
    check("browser evidence helper", (root / "skills/design-craft/scripts/design_craft_browser_evidence.py").is_file(), str(root / "skills/design-craft/scripts/design_craft_browser_evidence.py")),
    check("portable runtime", (root / "skills/design-craft/scripts/design_craft_route.sh").is_file(), str(root / "skills/design-craft/scripts")),
    check("platform scanner", (root / "skills/design-craft/scripts/design_craft_platform_scan.py").is_file(), str(root / "skills/design-craft/scripts/design_craft_platform_scan.py")),
    check("maturity scorer", (root / "scripts/design_craft_maturity.py").is_file(), str(root / "scripts/design_craft_maturity.py")),
    check("css smell scanner", (root / "skills/design-craft/scripts/design_craft_css_smell_scan.py").is_file(), str(root / "skills/design-craft/scripts/design_craft_css_smell_scan.py")),
    check("focus audit scanner", (root / "skills/design-craft/scripts/design_craft_focus_audit.py").is_file(), str(root / "skills/design-craft/scripts/design_craft_focus_audit.py")),
    check("token audit scanner", (root / "skills/design-craft/scripts/design_craft_token_audit.py").is_file(), str(root / "skills/design-craft/scripts/design_craft_token_audit.py")),
    check("skill version contract", bool(version) and version == skill_version, f"root={version or 'missing'} skill={skill_version or 'missing'}"),
    check(
        "skill compatibility contract",
        expected_route_schema == "design-craft.codex-route-pack.v2"
        and expected_manifest_schema == "codex.frontend-route-pack.manifest.v1"
        and expected_snapshot_schema == "codex.global_agents.snapshot.v2",
        str(root / "skills/design-craft/COMPATIBILITY.json"),
    ),
    installed_check("design-craft", root / "skills/design-craft"),
    check("python3", shutil.which("python3") is not None, shutil.which("python3") or "missing"),
    check("bash", shutil.which("bash") is not None, shutil.which("bash") or "missing"),
    check("target exists", target.exists(), str(target)),
    check("target writable", os.access(target if target.exists() else target.parent, os.W_OK), str(target)),
]

payload = {
    "root": str(root),
    "target": str(target),
    "ok": all(item["ok"] or not item["required"] for item in checks),
    "compatibility": {
        "expected_codex_route_pack_schema": expected_route_schema,
        "observed_codex_route_pack_schema": route_payload.get("schema"),
        "expected_route_pack_manifest_schema": expected_manifest_schema,
        "observed_route_pack_manifest_schema": route_pack_manifest.get("schema"),
        "expected_global_snapshot_schema": expected_snapshot_schema,
        "compatible": route_compatible,
    },
    "checks": checks,
}

if emit_json:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
else:
    print(f"design-craft doctor target: {target}")
    for item in checks:
        status = "found" if item["ok"] else "missing" if item["required"] else "optional-missing"
        print(f"- {item['name']}: {status} ({item['detail']})")
    print(f"overall_ok: {payload['ok']}")

sys.exit(0 if payload["ok"] else 1)
PY
