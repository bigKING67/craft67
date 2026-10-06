#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
source scripts/native_runtime_android_common.sh

SERIAL=""
EVIDENCE_DIR="${DESIGN_CRAFT_NATIVE_EVIDENCE_DIR:-}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --serial)
      SERIAL="${2:-}"
      shift 2
      ;;
    --evidence-dir)
      EVIDENCE_DIR="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

for command in adb gradle python3; do
  if ! command -v "${command}" >/dev/null 2>&1; then
    echo "Required command is unavailable: ${command}" >&2
    exit 1
  fi
done

if [[ -z "${EVIDENCE_DIR}" ]]; then
  EVIDENCE_DIR="$(mktemp -d -t design-craft-android-device.XXXXXX)"
fi
mkdir -p "${EVIDENCE_DIR}"
if [[ -e "${EVIDENCE_DIR}/real-device-observed.json" ]]; then
  echo "Evidence directory already contains real-device-observed.json: ${EVIDENCE_DIR}" >&2
  exit 1
fi

SERIAL="$(design_craft_select_physical_device "${SERIAL}")"
design_craft_assert_physical_device "${SERIAL}"
export ANDROID_SERIAL="${SERIAL}"

PROJECT_DIR="${EVIDENCE_DIR}/android-project"
if [[ -e "${PROJECT_DIR}" ]]; then
  echo "Evidence directory already contains an Android project: ${PROJECT_DIR}" >&2
  exit 1
fi
cp -R evals/native-runtime/fixtures/android "${PROJECT_DIR}"
gradle -p "${PROJECT_DIR}" :app:assembleDebug --no-daemon
apk="${PROJECT_DIR}/app/build/outputs/apk/debug/app-debug.apk"

adb wait-for-device
design_craft_prepare_device_ui
adb install -r "${apk}"
adb shell am force-stop dev.designcraft.runtimeevidence
adb shell am start -W -n dev.designcraft.runtimeevidence/.MainActivity > "${EVIDENCE_DIR}/launch.txt"
sleep 3
design_craft_dump_ui \
  "${EVIDENCE_DIR}" \
  "${EVIDENCE_DIR}/window-before.xml" \
  "Native runtime evidence title" \
  "dev.designcraft.runtimeevidence/.MainActivity"

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
  "dev.designcraft.runtimeevidence/.MainActivity"
adb exec-out screencap -p > "${EVIDENCE_DIR}/android-device.png"

python3 scripts/design_craft_native_runtime_record.py \
  --platform android \
  --runtime-kind android_device \
  --runtime-id "${SERIAL}" \
  --tool "Gradle/adb/UIAutomator physical device" \
  --command "gradle :app:assembleDebug" \
  --command "adb physical-device install and am start -W" \
  --command "UIAutomator dump, input tap, and screencap" \
  --assertion build_succeeded=true \
  --assertion install_and_launch_succeeded=true \
  --assertion accessibility_tree_observed=true \
  --assertion interaction_observed=true \
  --assertion screenshot_captured=true \
  --assertion physical_device_confirmed=true \
  --assertion device_authorization_confirmed=true \
  --artifact "before_accessibility_tree=${EVIDENCE_DIR}/window-before.xml" \
  --artifact "after_accessibility_tree=${EVIDENCE_DIR}/window-after.xml" \
  --artifact "after_screenshot=${EVIDENCE_DIR}/android-device.png" \
  --artifact "launch_log=${EVIDENCE_DIR}/launch.txt" \
  --fixture-root evals/native-runtime/fixtures/android \
  --output "${EVIDENCE_DIR}/real-device-observed.json"

python3 scripts/design_craft_native_runtime_validate.py \
  --validate \
  --root "${EVIDENCE_DIR}" \
  --require-real-device \
  --require-current-source \
  --json

echo "Android physical-device evidence captured in: ${EVIDENCE_DIR}"
