from __future__ import annotations

import json
import unittest

from tools.design_craft.release.native_ios_observation import (
    classify_observation,
    validate_success_log,
)


ATTEMPT = "live-30148003556-2"


def observation(
    *,
    marker: str = "Runtime interaction pending\n",
    url: bool = False,
    app: bool = False,
    openurl_exit: int = 0,
) -> dict[str, object]:
    events = ["launched"]
    if url:
        events.append(
            f"url-received:designcraft-evidence://confirm?attempt={ATTEMPT}"
        )
    if app:
        events.append(f"interaction-confirmed:{ATTEMPT}")
    return classify_observation(
        events_text="\n".join(events) + "\n",
        marker_text=marker,
        attempt=ATTEMPT,
        phase="live",
        poll=1,
        openurl_exit=openurl_exit,
    )


class NativeIosObservationTests(unittest.TestCase):
    def test_waits_for_url_before_fallback(self) -> None:
        result = observation()
        self.assertEqual(result["decision"], "waiting_for_url")
        self.assertTrue(result["fallback_allowed"])

    def test_url_without_app_confirmation_cannot_succeed(self) -> None:
        result = observation(url=True)
        self.assertEqual(result["decision"], "waiting_for_app_confirmation")
        self.assertFalse(result["fallback_allowed"])

    def test_app_confirmation_enters_marker_visibility_grace(self) -> None:
        result = observation(url=True, app=True)
        self.assertEqual(result["decision"], "marker_visibility_grace")
        self.assertFalse(result["fallback_allowed"])

    def test_delayed_marker_completes_the_same_attempt(self) -> None:
        states = [
            observation(),
            observation(url=True, app=True),
            observation(url=True, app=True),
            observation(
                marker=f"Runtime interaction confirmed attempt={ATTEMPT}\n",
                url=True,
                app=True,
            ),
        ]
        self.assertEqual(
            [state["decision"] for state in states],
            [
                "waiting_for_url",
                "marker_visibility_grace",
                "marker_visibility_grace",
                "fully_confirmed",
            ],
        )
        self.assertFalse(any(state["fallback_allowed"] for state in states[1:]))

    def test_openurl_timeout_is_diagnostic_after_delivery(self) -> None:
        result = observation(
            marker=f"Runtime interaction confirmed attempt={ATTEMPT}\n",
            url=True,
            app=True,
            openurl_exit=60,
        )
        self.assertEqual(result["decision"], "fully_confirmed")
        self.assertEqual(
            result["transport_warning"], "openurl_nonzero_after_delivery"
        )

    def test_foreign_attempt_marker_cannot_complete(self) -> None:
        result = observation(
            marker="Runtime interaction confirmed attempt=cold-other\n",
            url=True,
            app=True,
        )
        self.assertEqual(result["decision"], "marker_visibility_grace")
        self.assertEqual(result["marker_state"], "foreign")

    def test_success_log_requires_correlated_marker(self) -> None:
        result = observation(
            marker=f"Runtime interaction confirmed attempt={ATTEMPT}\n",
            url=True,
            app=True,
        )
        log = "\n".join(
            (
                "[poll observations]",
                json.dumps(result, sort_keys=True, separators=(",", ":")),
                "[system confirmation action] live:coordinate-tap-succeeded",
                "[confirmed interaction path] live-deep-link-system-confirmed",
            )
        )
        self.assertEqual(
            validate_success_log(
                log, f"Runtime interaction confirmed attempt={ATTEMPT}\n"
            ),
            [],
        )
        self.assertTrue(
            validate_success_log(
                log, "Runtime interaction confirmed attempt=foreign\n"
            )
        )


if __name__ == "__main__":
    unittest.main()
