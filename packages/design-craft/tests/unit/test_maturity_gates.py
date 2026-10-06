from __future__ import annotations

import unittest

from tools.design_craft.validation.maturity import development, evidence, repository
from tools.design_craft.validation.maturity.gates import (
    gate_runner,
    main_branch,
    performance_regression,
    route_pack,
)
from tools.design_craft.validation.maturity.profiles import (
    PHASES,
    PROFILE_NAMES,
    load_profile,
)


class MaturityGateRegistryTests(unittest.TestCase):
    def test_every_profile_gate_resolves(self) -> None:
        for profile_name in PROFILE_NAMES:
            for phase in PHASES:
                profile = load_profile(profile_name, phase)
                for gate_id in profile.required_gate_ids:
                    with self.subTest(
                        profile=profile_name,
                        phase=phase,
                        gate=gate_id,
                    ):
                        self.assertTrue(callable(gate_runner(gate_id)))

    def test_unknown_gate_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "no maturity gate runner"):
            gate_runner("unknown_gate")

    def test_compatibility_exports_preserve_gate_callables(self) -> None:
        self.assertIs(route_pack, development.route_pack)
        self.assertIs(performance_regression, evidence.performance_regression)
        self.assertIs(main_branch, repository.main_branch)


if __name__ == "__main__":
    unittest.main()
