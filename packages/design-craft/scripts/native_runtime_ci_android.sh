#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
source scripts/native_runtime_android_common.sh

EVIDENCE_DIR="${DESIGN_CRAFT_NATIVE_EVIDENCE_DIR:-${RUNNER_TEMP:-${TMPDIR:-/tmp}}/native-runtime-android}"
mkdir -p "${EVIDENCE_DIR}"
PACKAGE="dev.designcraft.runtimeevidence"
COMPONENT="${PACKAGE}/.MainActivity"

capture_android_diagnostics() {
  adb shell dumpsys activity activities > "${EVIDENCE_DIR}/activity-diagnostics.txt" 2>&1 || true
  adb shell dumpsys window windows > "${EVIDENCE_DIR}/window-diagnostics.txt" 2>&1 || true
}

wait_for_activity() {
  local attempt
  local activity_state
  local resumed_state

  for attempt in {1..20}; do
    activity_state="$(adb shell dumpsys activity activities 2>/dev/null || true)"
    resumed_state="$(grep -E 'mResumedActivity|topResumedActivity|ResumedActivity' <<< "${activity_state}" || true)"
    if grep -q "${PACKAGE}" <<< "${resumed_state}" \
      && grep -q "MainActivity" <<< "${resumed_state}"; then
      return 0
    fi
    if [[ "${attempt}" == "10" ]]; then
      adb shell am start -W -n "${COMPONENT}" >> "${EVIDENCE_DIR}/launch.txt" 2>&1 || true
    fi
    sleep 2
  done

  capture_android_diagnostics
  echo "Android evidence activity did not become resumed: ${COMPONENT}" >&2
  return 1
}

PROJECT_DIR="${EVIDENCE_DIR}/android-project"
rm -rf "${PROJECT_DIR}"
cp -R evals/native-runtime/fixtures/android "${PROJECT_DIR}"
gradle -p "${PROJECT_DIR}" :app:assembleDebug --no-daemon
apk="${PROJECT_DIR}/app/build/outputs/apk/debug/app-debug.apk"
if [[ "${DESIGN_CRAFT_NATIVE_BUILD_ONLY:-0}" == "1" ]]; then
  echo "Android fixture build verified: ${apk}"
  exit 0
fi
adb install -r "${apk}"
adb wait-for-device
design_craft_prepare_device_ui
adb shell settings put system screen_off_timeout 2147483647 || true
adb shell am force-stop "${PACKAGE}"
adb shell am start -W -n "${COMPONENT}" > "${EVIDENCE_DIR}/launch.txt"
wait_for_activity
design_craft_dump_ui \
  "${EVIDENCE_DIR}" \
  "${EVIDENCE_DIR}/window-before.xml" \
  "Native runtime evidence title" \
  "${COMPONENT}"

read -r tap_x tap_y < <(python3 - "${EVIDENCE_DIR}/window-before.xml" <<'PY'
import re
import sys
import xml.etree.ElementTree as ET

root = ET.parse(sys.argv[1]).getroot()
for node in root.iter("node"):
    if node.attrib.get("content-desc") == "Confirm native runtime":
        match = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", node.attrib["bounds"])
        if not match:
            break
        left, top, right, bottom = map(int, match.groups())
        print((left + right) // 2, (top + bottom) // 2)
        raise SystemExit(0)
raise SystemExit("Confirm runtime button not found")
PY
)
adb shell input tap "${tap_x}" "${tap_y}"
design_craft_dump_ui \
  "${EVIDENCE_DIR}" \
  "${EVIDENCE_DIR}/window-after.xml" \
  "Runtime interaction confirmed" \
  "${COMPONENT}"
adb exec-out screencap -p > "${EVIDENCE_DIR}/android-emulator.png"

python3 scripts/design_craft_native_runtime_record.py \
  --platform android \
  --runtime-kind android_emulator \
  --runtime-id "$(adb get-serialno)" \
  --tool "Gradle/adb/UIAutomator" \
  --command "gradle :app:assembleDebug" \
  --command "adb install and am start -W" \
  --command "UIAutomator dump, input tap, and screencap" \
  --assertion build_succeeded=true \
  --assertion install_and_launch_succeeded=true \
  --assertion accessibility_tree_observed=true \
  --assertion interaction_observed=true \
  --assertion screenshot_captured=true \
  --artifact "before_accessibility_tree=${EVIDENCE_DIR}/window-before.xml" \
  --artifact "after_accessibility_tree=${EVIDENCE_DIR}/window-after.xml" \
  --artifact "after_screenshot=${EVIDENCE_DIR}/android-emulator.png" \
  --artifact "launch_log=${EVIDENCE_DIR}/launch.txt" \
  --fixture-root evals/native-runtime/fixtures/android \
  --output "${EVIDENCE_DIR}/android-observed.json"
python3 scripts/design_craft_native_runtime_validate.py \
  --validate \
  --root "${EVIDENCE_DIR}" \
  --require android \
  --require-current-source \
  --json
