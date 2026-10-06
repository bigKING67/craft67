from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ATTEMPT_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
CONFIRMED_PREFIX = "Runtime interaction confirmed attempt="
PENDING_MARKER = "Runtime interaction pending"
SUCCESS_DECISION = "fully_confirmed"


def read_optional(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def classify_observation(
    *,
    events_text: str,
    marker_text: str,
    attempt: str,
    phase: str,
    poll: int,
    openurl_exit: int,
) -> dict[str, object]:
    if ATTEMPT_PATTERN.fullmatch(attempt) is None:
        raise ValueError("attempt must contain only bounded safe identifier characters")
    if phase not in {"live", "cold"}:
        raise ValueError("phase must be live or cold")
    if poll <= 0:
        raise ValueError("poll must be positive")

    attempt_query = f"attempt={attempt}"
    url_receipt = any(
        line.startswith("url-received:designcraft-evidence:")
        and attempt_query in line
        for line in events_text.splitlines()
    )
    app_confirmation = (
        f"interaction-confirmed:{attempt}" in events_text.splitlines()
    )
    expected_marker = f"{CONFIRMED_PREFIX}{attempt}"
    marker_confirmed = expected_marker in marker_text.splitlines()
    marker_exists = bool(marker_text)
    if marker_confirmed:
        marker_state = "confirmed"
    elif PENDING_MARKER in marker_text:
        marker_state = "pending"
    elif marker_text:
        marker_state = "foreign"
    else:
        marker_state = "missing"

    if url_receipt and app_confirmation and marker_confirmed:
        decision = SUCCESS_DECISION
    elif url_receipt and app_confirmation:
        decision = "marker_visibility_grace"
    elif url_receipt:
        decision = "waiting_for_app_confirmation"
    elif app_confirmation:
        decision = "correlation_failure"
    else:
        decision = "waiting_for_url"

    return {
        "schema": "design-craft.native-ios-poll.v1",
        "phase": phase,
        "attempt": attempt,
        "poll": poll,
        "openurl_exit": openurl_exit,
        "url_receipt": url_receipt,
        "app_confirmation": app_confirmation,
        "marker_exists": marker_exists,
        "marker_state": marker_state,
        "marker_confirmed": marker_confirmed,
        "decision": decision,
        "fallback_allowed": not url_receipt and not app_confirmation,
        "transport_warning": (
            "openurl_nonzero_after_delivery"
            if openurl_exit != 0 and url_receipt
            else None
        ),
    }


def observe_files(
    *,
    events_path: Path,
    marker_path: Path,
    attempt: str,
    phase: str,
    poll: int,
    openurl_exit: int,
) -> dict[str, object]:
    return classify_observation(
        events_text=read_optional(events_path),
        marker_text=read_optional(marker_path),
        attempt=attempt,
        phase=phase,
        poll=poll,
        openurl_exit=openurl_exit,
    )


def append_observation(path: Path, observation: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                observation,
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        )


def validate_success_log(log_text: str, marker_text: str) -> list[str]:
    errors: list[str] = []
    observations: list[dict[str, object]] = []
    in_poll_section = False
    for line in log_text.splitlines():
        if line == "[poll observations]":
            in_poll_section = True
            continue
        if in_poll_section and line.startswith("["):
            in_poll_section = False
        if not in_poll_section or not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            errors.append("poll observation contains invalid JSON")
            continue
        if isinstance(payload, dict):
            observations.append(payload)
    successes = [
        item
        for item in observations
        if item.get("decision") == SUCCESS_DECISION
        and item.get("url_receipt") is True
        and item.get("app_confirmation") is True
        and item.get("marker_confirmed") is True
    ]
    if not successes:
        errors.append("launch log must contain a fully confirmed poll observation")
        return errors
    final = successes[-1]
    attempt = final.get("attempt")
    if not isinstance(attempt, str) or f"{CONFIRMED_PREFIX}{attempt}" not in marker_text:
        errors.append("interaction marker must match the successful poll attempt")
    if "[system confirmation action]" not in log_text:
        errors.append("launch log must record the system confirmation action")
    if "[confirmed interaction path]" not in log_text:
        errors.append("launch log must record the confirmed interaction path")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", required=True)
    parser.add_argument("--marker", required=True)
    parser.add_argument("--attempt", required=True)
    parser.add_argument("--phase", choices=("live", "cold"), required=True)
    parser.add_argument("--poll", type=int, required=True)
    parser.add_argument("--openurl-exit", type=int, required=True)
    parser.add_argument("--append", required=True)
    args = parser.parse_args()
    try:
        observation = observe_files(
            events_path=Path(args.events),
            marker_path=Path(args.marker),
            attempt=args.attempt,
            phase=args.phase,
            poll=args.poll,
            openurl_exit=args.openurl_exit,
        )
    except ValueError as exc:
        parser.error(str(exc))
    append_observation(Path(args.append), observation)
    print(observation["decision"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
