#!/usr/bin/env bash

design_craft_dismiss_blocking_dialog() {
  local xml_path="$1"
  local coordinates
  coordinates="$(python3 - "${xml_path}" <<'PY'
import re
import sys
import xml.etree.ElementTree as ET

root = ET.parse(sys.argv[1]).getroot()
for node in root.iter("node"):
    if node.attrib.get("resource-id") != "android:id/aerr_close":
        continue
    match = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", node.attrib.get("bounds", ""))
    if match:
        left, top, right, bottom = map(int, match.groups())
        print((left + right) // 2, (top + bottom) // 2)
        raise SystemExit(0)
raise SystemExit(1)
PY
)" || return 1
  read -r tap_x tap_y <<< "${coordinates}"
  adb shell input tap "${tap_x}" "${tap_y}"
}

design_craft_dump_ui() {
  local evidence_dir="$1"
  local output="$2"
  local expected_text="${3:-}"
  local relaunch_component="${4:-}"
  local label
  label="$(basename "${output}" .xml)"
  local remote_path="/data/local/tmp/design-craft-${label}.xml"
  local temporary="${output}.tmp"
  local dump_log="${evidence_dir}/uiautomator-${label}.log"
  local attempt

  : > "${dump_log}"
  for attempt in {1..10}; do
    rm -f "${temporary}"
    printf 'attempt=%s\n' "${attempt}" >> "${dump_log}"
    adb shell rm -f "${remote_path}" >/dev/null 2>&1 || true
    if adb shell uiautomator dump --compressed "${remote_path}" >> "${dump_log}" 2>&1 \
      && adb exec-out cat "${remote_path}" > "${temporary}" 2>> "${dump_log}" \
      && python3 - "${temporary}" 2>> "${dump_log}" <<'PY'
import sys
import xml.etree.ElementTree as ET

ET.parse(sys.argv[1])
PY
    then
      adb shell rm -f "${remote_path}" >/dev/null 2>&1 || true
      if [[ -n "${expected_text}" ]] && ! grep -q -- "${expected_text}" "${temporary}"; then
        if design_craft_dismiss_blocking_dialog "${temporary}"; then
          printf '%s\n' 'dismissed blocking system dialog' >> "${dump_log}"
          if [[ -n "${relaunch_component}" ]]; then
            adb shell am start -W -n "${relaunch_component}" \
              >> "${evidence_dir}/relaunch.txt" 2>&1 || true
          fi
        fi
        sleep 3
        continue
      fi
      mv "${temporary}" "${output}"
      return 0
    fi
    sleep 3
  done

  adb shell rm -f "${remote_path}" >/dev/null 2>&1 || true
  adb shell dumpsys window windows > "${evidence_dir}/window-diagnostics.txt" 2>&1 || true
  echo "Unable to capture a stable UIAutomator tree containing: ${expected_text}" >&2
  return 1
}

design_craft_select_physical_device() {
  local requested="${1:-}"
  local listing
  listing="$(mktemp -t design-craft-adb-devices.XXXXXX)"
  adb devices -l > "${listing}"
  local status=0
  if python3 - "${listing}" "${requested}" <<'PY'
import sys
from pathlib import Path

listing = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
requested = sys.argv[2]
devices = []
for line in listing.splitlines()[1:]:
    if "\tdevice" not in line:
        continue
    serial = line.split("\t", 1)[0].strip()
    if serial and not serial.startswith("emulator-"):
        devices.append(serial)
if requested:
    if requested not in devices:
        raise SystemExit("Requested physical Android device is not connected and authorized")
    print(requested)
elif len(devices) == 1:
    print(devices[0])
elif not devices:
    raise SystemExit("No authorized physical Android device is connected")
else:
    raise SystemExit("Multiple physical Android devices are connected; pass --serial")
PY
  then
    status=0
  else
    status=$?
  fi
  rm -f "${listing}"
  return "${status}"
}

design_craft_assert_physical_device() {
  local serial="$1"
  local qemu
  qemu="$(adb -s "${serial}" shell getprop ro.kernel.qemu | tr -d '\r')"
  if [[ "${qemu}" == "1" || "${serial}" == emulator-* ]]; then
    echo "Refusing to record an emulator as physical-device evidence" >&2
    return 1
  fi
  adb -s "${serial}" get-state | grep -qx "device"
}

design_craft_prepare_device_ui() {
  adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1 || true
  adb shell wm dismiss-keyguard >/dev/null 2>&1 || true
  adb shell am wait-for-broadcast-idle >/dev/null 2>&1 || true
}
