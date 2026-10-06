#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

EVIDENCE_DIR="${DESIGN_CRAFT_NATIVE_EVIDENCE_DIR:-${RUNNER_TEMP:-${TMPDIR:-/tmp}}/native-runtime-ios}"
APP_DIR="${EVIDENCE_DIR}/DesignCraftEvidence.app"
AXE_VERSION="1.7.1"
AXE_ARCHIVE_SHA256="26a64009c09a3ae980b1f1b4b377bd2a2dd96cbbde24821935e47352cb71cc69"
AXE_TOOL_DIR="${RUNNER_TEMP:-${TMPDIR:-/tmp}}/design-craft-axe-v${AXE_VERSION}"
AXE_BIN="${AXE_TOOL_DIR}/axe"
mkdir -p "${APP_DIR}"
cp evals/native-runtime/fixtures/ios/Info.plist "${APP_DIR}/Info.plist"

sdk_path="$(xcrun --sdk iphonesimulator --show-sdk-path)"
deployment_target="$(/usr/libexec/PlistBuddy -c 'Print :MinimumOSVersion' evals/native-runtime/fixtures/ios/Info.plist)"
arch="$(uname -m)"
xcrun --sdk iphonesimulator swiftc \
  -parse-as-library \
  -module-name DesignCraftEvidence \
  -sdk "${sdk_path}" \
  -target "${arch}-apple-ios${deployment_target}-simulator" \
  -framework UIKit \
  evals/native-runtime/fixtures/ios/App.swift \
  -o "${APP_DIR}/DesignCraftEvidence"
codesign --force --sign - "${APP_DIR}"

if [[ "${DESIGN_CRAFT_NATIVE_BUILD_ONLY:-0}" == "1" ]]; then
  echo "iOS fixture build verified: ${APP_DIR}"
  exit 0
fi

selection="$(xcrun simctl list devices available -j | python3 -c '
import json
import re
import sys

payload = json.load(sys.stdin)
candidates = []
for runtime, devices in payload.get("devices", {}).items():
    match = re.search(r"\.iOS-([0-9-]+)$", runtime)
    if not match:
        continue
    version = tuple(int(part) for part in match.group(1).split("-"))
    for device in devices:
        name = str(device.get("name", ""))
        device_type = str(device.get("deviceTypeIdentifier", ""))
        if device.get("isAvailable") and name.startswith("iPhone") and device_type:
            preferred = int("Pro" in name and "Max" not in name)
            candidates.append((version, preferred, name, runtime, device_type))
if not candidates:
    raise SystemExit("No available iPhone Simulator")
selected = max(candidates)
print(f"{selected[3]}\t{selected[4]}")
')"
IFS=$'\t' read -r runtime_identifier device_type_identifier <<< "${selection}"
printf 'runtime=%s\ndevice_type=%s\n' \
  "${runtime_identifier}" \
  "${device_type_identifier}" \
  > "${EVIDENCE_DIR}/simulator-selection.txt"
simulator_name="Design Craft Evidence ${GITHUB_RUN_ID:-$$}"
udid="$(xcrun simctl create \
  "${simulator_name}" \
  "${device_type_identifier}" \
  "${runtime_identifier}")"
cleanup_simulator() {
  xcrun simctl shutdown "${udid}" >/dev/null 2>&1 || true
  xcrun simctl delete "${udid}" >/dev/null 2>&1 || true
}
trap cleanup_simulator EXIT
xcrun simctl boot "${udid}"
xcrun simctl bootstatus "${udid}" -b
xcrun simctl install "${udid}" "${APP_DIR}"
xcrun simctl launch "${udid}" dev.designcraft.runtime-evidence > "${EVIDENCE_DIR}/launch.txt"
sleep 2
xcrun simctl io "${udid}" screenshot "${EVIDENCE_DIR}/ios-before-interaction.png"
data_container="$(xcrun simctl get_app_container "${udid}" dev.designcraft.runtime-evidence data)"
interaction_marker="${data_container}/Documents/runtime-interaction.txt"
runtime_events="${data_container}/Documents/runtime-events.txt"
poll_observations="${EVIDENCE_DIR}/runtime-poll-observations.jsonl"
: > "${poll_observations}"
poll_sequence=0
refresh_runtime_paths() {
  data_container="$(xcrun simctl get_app_container "${udid}" dev.designcraft.runtime-evidence data)"
  interaction_marker="${data_container}/Documents/runtime-interaction.txt"
  runtime_events="${data_container}/Documents/runtime-events.txt"
}
copy_runtime_events() {
  if [[ -f "${runtime_events}" ]]; then
    cp "${runtime_events}" "${EVIDENCE_DIR}/runtime-events.txt"
  fi
}
wait_for_interaction() {
  local phase="$1"
  local attempt_token="$2"
  local openurl_exit="$3"
  local max_attempts="${4:-15}"
  local poll
  local decision="waiting_for_url"
  for ((poll = 1; poll <= max_attempts; poll++)); do
    poll_sequence=$((poll_sequence + 1))
    decision="$(python3 -m tools.design_craft.release.native_ios_observation \
      --events "${runtime_events}" \
      --marker "${interaction_marker}" \
      --attempt "${attempt_token}" \
      --phase "${phase}" \
      --poll "${poll_sequence}" \
      --openurl-exit "${openurl_exit}" \
      --append "${poll_observations}")"
    if [[ "${decision}" == "fully_confirmed" ]]; then
      return 0
    fi
    if [[ "${decision}" == "marker_visibility_grace" ]]; then
      refresh_runtime_paths
    fi
    sleep 2
  done
  if [[ "${decision}" != "waiting_for_url" ]]; then
    return 2
  fi
  return 1
}
ensure_axe() {
  local archive="${AXE_TOOL_DIR}/AXe-macOS-v${AXE_VERSION}-universal.tar.gz"
  local actual_sha256
  if [[ ! -x "${AXE_BIN}" ]]; then
    mkdir -p "${AXE_TOOL_DIR}"
    curl --fail --location --retry 3 --retry-all-errors \
      "https://github.com/cameroncooke/AXe/releases/download/v${AXE_VERSION}/AXe-macOS-v${AXE_VERSION}-universal.tar.gz" \
      --output "${archive}"
    actual_sha256="$(shasum -a 256 "${archive}" | awk '{print $1}')"
    if [[ "${actual_sha256}" != "${AXE_ARCHIVE_SHA256}" ]]; then
      echo "AXe archive checksum mismatch: ${actual_sha256}" >&2
      return 1
    fi
    tar -xzf "${archive}" -C "${AXE_TOOL_DIR}"
  fi
  "${AXE_BIN}" --version > "${EVIDENCE_DIR}/axe-version.txt" 2>&1
}
confirmation_tap_point() {
  local screenshot="$1"
  python3 - "${screenshot}" <<'PY'
import struct
import sys

with open(sys.argv[1], "rb") as stream:
    header = stream.read(24)
if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
    raise SystemExit("confirmation screenshot is not a PNG")

pixel_width, pixel_height = struct.unpack(">II", header[16:24])
for scale in (3.0, 2.0, 1.0):
    point_width = pixel_width / scale
    point_height = pixel_height / scale
    if 300 <= point_width <= 500 and 550 <= point_height <= 1000:
        break
else:
    raise SystemExit("unsupported Simulator screenshot dimensions")

# The system alert is centered; Open is the right-hand button below its title.
tap_x = point_width * 0.685
tap_y = point_height * 0.5 + 37.0
print(f"{tap_x:.1f}\t{tap_y:.1f}\t{scale:g}")
PY
}
system_confirmation_action="not-attempted"
attempt_deep_link() {
  local phase="$1"
  local url="$2"
  local output="$3"
  local attempt_token="$4"
  local confirmation_screenshot="${EVIDENCE_DIR}/ios-${phase}-open-confirmation.png"
  local openurl_exit=0
  local wait_status=1
  local tap_point=""
  local tap_x=""
  local tap_y=""
  local tap_scale=""
  system_confirmation_action="not-attempted"
  set +e
  xcrun simctl openurl "${udid}" "${url}" > "${output}" 2>&1
  openurl_exit=$?
  set -e
  printf '%s\n' "${openurl_exit}" > "${EVIDENCE_DIR}/openurl-${phase}-exit.txt"
  if wait_for_interaction "${phase}" "${attempt_token}" "${openurl_exit}" 3; then
    return 0
  else
    wait_status=$?
  fi
  if ((wait_status == 2)); then
    if wait_for_interaction "${phase}" "${attempt_token}" "${openurl_exit}" 12; then
      return 0
    else
      wait_status=$?
    fi
    return "${wait_status}"
  fi

  xcrun simctl io "${udid}" screenshot \
    "${confirmation_screenshot}" \
    >/dev/null 2>&1 || true
  if ensure_axe; then
    if "${AXE_BIN}" tap --label "Open" --element-type Button \
      --wait-timeout 5 --udid "${udid}" \
      > "${EVIDENCE_DIR}/axe-${phase}-tap.log" 2>&1; then
      system_confirmation_action="${phase}:AXe-v${AXE_VERSION}-label-succeeded"
      if wait_for_interaction "${phase}" "${attempt_token}" "${openurl_exit}" 12; then
        return 0
      else
        wait_status=$?
      fi
      if ((wait_status == 2)); then
        return 2
      fi
    else
      system_confirmation_action="${phase}:AXe-v${AXE_VERSION}-label-failed"
    fi

    if tap_point="$(confirmation_tap_point "${confirmation_screenshot}")"; then
      IFS=$'\t' read -r tap_x tap_y tap_scale <<< "${tap_point}"
      printf 'x=%s\ny=%s\nscale=%s\n' \
        "${tap_x}" "${tap_y}" "${tap_scale}" \
        > "${EVIDENCE_DIR}/axe-${phase}-coordinate.txt"
      if "${AXE_BIN}" tap -x "${tap_x}" -y "${tap_y}" \
        --tap-style simulator --pre-delay 0.5 --post-delay 0.5 \
        --udid "${udid}" \
        > "${EVIDENCE_DIR}/axe-${phase}-coordinate-tap.log" 2>&1; then
        system_confirmation_action="${phase}:AXe-v${AXE_VERSION}-coordinate-succeeded"
        if wait_for_interaction "${phase}" "${attempt_token}" "${openurl_exit}" 12; then
          return 0
        else
          wait_status=$?
        fi
        if ((wait_status == 2)); then
          return 2
        fi
      else
        system_confirmation_action="${phase}:AXe-v${AXE_VERSION}-coordinate-failed"
      fi
    fi
  fi

  xcrun simctl io "${udid}" screenshot \
    "${EVIDENCE_DIR}/ios-${phase}-deep-link-timeout.png" \
    >/dev/null 2>&1 || true
  return 1
}

interaction_path=""
live_attempt="live-${GITHUB_RUN_ID:-local}-${GITHUB_RUN_ATTEMPT:-1}"
cold_attempt="cold-${GITHUB_RUN_ID:-local}-${GITHUB_RUN_ATTEMPT:-1}"
if attempt_deep_link \
  live \
  "designcraft-evidence://confirm?attempt=${live_attempt}" \
  "${EVIDENCE_DIR}/openurl-live.txt" \
  "${live_attempt}"; then
  interaction_path="live-deep-link"
else
  live_status=$?
  if ((live_status == 1)); then
    xcrun simctl terminate "${udid}" dev.designcraft.runtime-evidence || true
    if attempt_deep_link \
      cold \
      "designcraft-evidence:///confirm?attempt=${cold_attempt}" \
      "${EVIDENCE_DIR}/openurl-cold.txt" \
      "${cold_attempt}"; then
      interaction_path="cold-deep-link"
    fi
  fi
fi
if [[ -n "${interaction_path}" && "${system_confirmation_action}" == *-succeeded ]]; then
  interaction_path="${interaction_path}-system-confirmed"
fi

copy_runtime_events
{
  printf '%s\n' '[initial launch]'
  cat "${EVIDENCE_DIR}/launch.txt"
  printf '%s\n' '[live deep link]'
  cat "${EVIDENCE_DIR}/openurl-live.txt" 2>/dev/null || true
  if [[ -f "${EVIDENCE_DIR}/openurl-cold.txt" ]]; then
    printf '%s\n' '[cold deep link fallback]'
    cat "${EVIDENCE_DIR}/openurl-cold.txt"
  fi
  printf '%s\n' '[application events]'
  cat "${EVIDENCE_DIR}/runtime-events.txt" 2>/dev/null || true
  printf '%s\n' '[poll observations]'
  cat "${poll_observations}" 2>/dev/null || true
  printf '%s\n' "[system confirmation action] ${system_confirmation_action}"
  printf '%s\n' "[confirmed interaction path] ${interaction_path:-none}"
} > "${EVIDENCE_DIR}/runtime-launch.log"

if [[ -z "${interaction_path}" ]]; then
  xcrun simctl spawn "${udid}" log show --last 3m --info --debug \
    --predicate 'process == "DesignCraftEvidence" OR eventMessage CONTAINS[c] "designcraft" OR eventMessage CONTAINS[c] "openurl"' \
    > "${EVIDENCE_DIR}/interaction-diagnostics.log" 2>&1 || true
  echo "iOS runtime deep link did not produce one correlated URL, app confirmation, and marker receipt" >&2
  exit 1
fi
cp "${interaction_marker}" "${EVIDENCE_DIR}/runtime-interaction.txt"
xcrun simctl io "${udid}" screenshot "${EVIDENCE_DIR}/ios-after-interaction.png"

python3 scripts/design_craft_native_runtime_record.py \
  --platform ios \
  --runtime-kind ios_simulator \
  --runtime-id "${udid}" \
  --tool "xcrun simctl/AXe v${AXE_VERSION}" \
  --command "xcrun swiftc iOS fixture" \
  --command "xcrun simctl boot/install/launch" \
  --command "xcrun simctl openurl plus pinned AXe semantic/coordinate system confirmation" \
  --command "live/cold deep-link interaction, URL receipt, and marker assertion" \
  --command "xcrun simctl io before/after screenshots" \
  --assertion build_succeeded=true \
  --assertion install_and_launch_succeeded=true \
  --assertion runtime_interaction_observed=true \
  --assertion before_and_after_screenshots_captured=true \
  --artifact "before_screenshot=${EVIDENCE_DIR}/ios-before-interaction.png" \
  --artifact "after_screenshot=${EVIDENCE_DIR}/ios-after-interaction.png" \
  --artifact "interaction_marker=${EVIDENCE_DIR}/runtime-interaction.txt" \
  --artifact "launch_log=${EVIDENCE_DIR}/runtime-launch.log" \
  --fixture-root evals/native-runtime/fixtures/ios \
  --output "${EVIDENCE_DIR}/ios-observed.json"
python3 scripts/design_craft_native_runtime_validate.py \
  --validate \
  --root "${EVIDENCE_DIR}" \
  --require ios \
  --require-current-source \
  --json
