from __future__ import annotations

import unittest

from scripts.design_craft_workflow_validate import (
    benchmark_artifact_contract_errors,
)


def benchmark_fixture(*, output: str, make_input: str, evidence: str) -> str:
    return f"""jobs:
  operational-candidate:
    steps:
      - run: python3 -m tools.design_craft benchmark --output {output}
      - run: make release-readiness-operational {make_input} {evidence}
      - uses: actions/upload-artifact@{'a' * 40}
        with:
          path: |
            ${{{{ runner.temp }}}}/operational-candidate/benchmark-result-full.json
            ${{{{ runner.temp }}}}/operational-candidate/dist/evidence/operational-95-candidate.json
"""


CERTIFY_FIXTURE = """jobs:
  certify:
    steps:
      - run: |
          BENCHMARK_RESULT=${RUNNER_TEMP}/benchmark/benchmark-result-full.json
          test -f "${BENCHMARK_RESULT}"
          test -f "${RUNNER_TEMP}/benchmark/dist/evidence/operational-95-candidate.json"
"""


class WorkflowArtifactContractTests(unittest.TestCase):
    def test_accepts_external_staging_with_stable_archive_layout(self) -> None:
        benchmark = benchmark_fixture(
            output='"${RUNNER_TEMP}/operational-candidate/benchmark-result-full.json"',
            make_input='BENCHMARK_RESULT="${RUNNER_TEMP}/operational-candidate/benchmark-result-full.json"',
            evidence='OPERATIONAL_CANDIDATE_EVIDENCE="${RUNNER_TEMP}/operational-candidate/dist/evidence/operational-95-candidate.json"',
        )
        self.assertEqual(
            benchmark_artifact_contract_errors(benchmark, CERTIFY_FIXTURE), []
        )

    def test_rejects_checkout_relative_benchmark_output(self) -> None:
        benchmark = benchmark_fixture(
            output="benchmark-result-full.json",
            make_input='BENCHMARK_RESULT="${RUNNER_TEMP}/operational-candidate/benchmark-result-full.json"',
            evidence='OPERATIONAL_CANDIDATE_EVIDENCE="${RUNNER_TEMP}/operational-candidate/dist/evidence/operational-95-candidate.json"',
        )
        errors = benchmark_artifact_contract_errors(benchmark, CERTIFY_FIXTURE)
        self.assertTrue(any("source checkout" in error for error in errors))

    def test_rejects_checkout_relative_make_input(self) -> None:
        benchmark = benchmark_fixture(
            output='"${RUNNER_TEMP}/operational-candidate/benchmark-result-full.json"',
            make_input="BENCHMARK_RESULT=benchmark-result-full.json",
            evidence='OPERATIONAL_CANDIDATE_EVIDENCE="${RUNNER_TEMP}/operational-candidate/dist/evidence/operational-95-candidate.json"',
        )
        errors = benchmark_artifact_contract_errors(benchmark, CERTIFY_FIXTURE)
        self.assertTrue(any("source checkout" in error for error in errors))

    def test_rejects_candidate_consumer_layout_drift(self) -> None:
        drifted = CERTIFY_FIXTURE.replace(
            "benchmark/dist/evidence/operational-95-candidate.json",
            "benchmark/operational-95-candidate.json",
        )
        benchmark = benchmark_fixture(
            output='"${RUNNER_TEMP}/operational-candidate/benchmark-result-full.json"',
            make_input='BENCHMARK_RESULT="${RUNNER_TEMP}/operational-candidate/benchmark-result-full.json"',
            evidence='OPERATIONAL_CANDIDATE_EVIDENCE="${RUNNER_TEMP}/operational-candidate/dist/evidence/operational-95-candidate.json"',
        )
        errors = benchmark_artifact_contract_errors(benchmark, drifted)
        self.assertTrue(any("consumer" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
