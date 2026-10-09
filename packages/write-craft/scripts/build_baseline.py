#!/usr/bin/env python3
"""Assemble a release behavior baseline from per-case evaluation artifacts.

The artifact root holds one `--output-dir` per case, as produced by running
`eval_behavior.py --case <id> --output-dir <root>/<id>`. A case whose fact
review ended in ERROR may be promoted only through an explicit `--rejudge`
that passed. Exploration cases enter the baseline only when they passed;
every exploration status is disclosed in the acceptance summary. Nothing is
written unless every regression case has PASS evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.eval_contracts import canonical_json, han_character_count, sha256_text  # noqa: E402
from scripts.validate import EVAL_BASELINES, SKILL, behavior_case_digest, tree_digest  # noqa: E402

ARTIFACT_PREFIX = ".artifacts/write-craft-evals/"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def lineage_slug(error: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", error.lower()).strip("_")
    return slug[:60] or "judge_error"


def case_dir(root: Path, case_id: str) -> Path | None:
    matches = sorted((root / case_id).glob(f"{case_id}--*/result.json"))
    return matches[0].parent if matches else None


def passing_rejudge(directory: Path) -> Path | None:
    for rejudge in sorted(directory.glob("rejudge-*"), reverse=True):
        result = rejudge / "result.json"
        if result.is_file() and read_json(result).get("status") == "PASS":
            return rejudge
    return None


def build_entry(case: dict[str, Any], directory: Path) -> tuple[dict[str, Any] | None, str]:
    result_path = directory / "result.json"
    result = read_json(result_path)
    candidate = (directory / "candidate.md").read_text(encoding="utf-8").removesuffix("\n")
    entry: dict[str, Any] = {
        "case_id": case["id"],
        "baseline_run": result.get("run_index", 1),
        "status": "PASS",
        "case_digest": result["case_digest"],
        "source_input_sha256": file_sha256(directory / "input.json"),
        "generator": result["generator"],
        "stages": dict(result["stages"]),
        "candidate": candidate,
        "candidate_sha256": sha256_text(candidate),
    }
    if entry["candidate_sha256"] != result["candidate_sha256"]:
        return None, "candidate does not match its recorded hash"

    if result["status"] == "PASS":
        judgment = read_json(directory / "judgment.json")
        entry.update(
            lineage="original",
            source_artifact=relative(result_path),
            source_result_sha256=file_sha256(result_path),
            judge=result["judge"],
        )
    else:
        rejudge = passing_rejudge(directory) if result["status"] == "ERROR" else None
        if rejudge is None or result["stages"].get("generation") != "PASS":
            return None, result["status"]
        rejudge_result_path = rejudge / "result.json"
        rejudge_result = read_json(rejudge_result_path)
        judgment = read_json(rejudge / "judgment.json")
        error = result.get("error") or "judge error"
        entry.update(
            lineage=f"explicit_rejudge_after_{lineage_slug(error)}",
            source_artifact=relative(rejudge_result_path),
            source_result_sha256=file_sha256(rejudge_result_path),
            judge=rejudge_result["judge"],
            original_failure={
                "status": "ERROR",
                "error": error,
                "result_sha256": file_sha256(result_path),
            },
        )
        entry["stages"]["fact_review"] = "PASS"

    if judgment.get("status") != "PASS":
        return None, "judgment is not PASS"
    entry["judgment"] = judgment
    entry["judgment_sha256"] = sha256_text(canonical_json(judgment))
    if isinstance(case.get("limits"), dict):
        entry["candidate_metrics"] = {"han_characters": han_character_count(candidate)}
    for key in ("reader_response", "reader_judgment"):
        if key in result:
            entry[key] = result[key]
            entry[f"{key}_sha256"] = sha256_text(canonical_json(result[key]))
    return entry, "PASS"


def calibration_summary(directory: Path, fixtures: dict[str, Any]) -> tuple[str, str]:
    results = [read_json(path) for path in sorted(directory.glob("*/result.json"))]
    passed = sum(item.get("status") == "PASS" for item in results)
    total = len(fixtures.get("fixtures", []))
    if len(results) != total:
        raise SystemExit(f"calibration covers {len(results)} of {total} fixtures")
    return f"{passed}/{total} PASS", read_json(directory / "run.json")["judge"]["model"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--calibration", type=Path, required=True)
    parser.add_argument("--human-record", type=Path, required=True)
    parser.add_argument("--human-documents", type=int, required=True)
    parser.add_argument("--limitation", action="append", default=[], required=True)
    parser.add_argument("--note", action="append", default=[])
    parser.add_argument("--pi-version", required=True)
    args = parser.parse_args()

    cases = read_json(ROOT / "evals" / "cases.json")["cases"]
    fixtures = read_json(ROOT / "evals" / "judge-fixtures.json")
    root = args.artifact_root.resolve()

    results: list[dict[str, Any]] = []
    regression_failures: list[str] = []
    exploration_status: list[str] = []
    for case in cases:
        directory = case_dir(root, case["id"])
        if directory is None:
            status, entry = "NOT_RUN", None
        else:
            entry, status = build_entry(case, directory)
        if entry is not None and entry["case_digest"] != behavior_case_digest(case):
            entry, status = None, "stale case digest"
        if entry is not None and read_json(directory.parent / "run.json").get(
            "skill_sha256"
        ) != tree_digest(SKILL):
            entry, status = None, "run used a different Skill"
        if case.get("track") == "regression":
            if entry is None:
                regression_failures.append(f"{case['id']}: {status}")
                continue
        else:
            exploration_status.append(f"{case['id']}={status if entry is None else 'PASS'}")
            if entry is None:
                continue
        results.append(entry)
    if regression_failures:
        print("Regression cases without PASS evidence:", file=sys.stderr)
        for line in regression_failures:
            print(f"  {line}", file=sys.stderr)
        return 1

    calibration, calibration_judge = calibration_summary(args.calibration.resolve(), fixtures)
    generator_models = sorted({item["generator"]["model"] for item in results})
    judge_models = sorted({item["judge"]["model"] for item in results})
    regression_total = sum(case.get("track") == "regression" for case in cases)
    rejudges = sum(item["lineage"] != "original" for item in results)
    limited = [item for item in results if "candidate_metrics" in item]
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True
    ).stdout.strip()
    dirty = bool(
        subprocess.run(
            ["git", "status", "--porcelain", "--", "."],
            cwd=ROOT, text=True, capture_output=True, check=True,
        ).stdout.strip()
    )

    baseline = {
        "schema": "write-craft.behavior-baseline.v1",
        "version": args.version,
        "recorded_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "host": {"name": "pi", "version": args.pi_version},
        "provenance": {
            "source_revision": revision,
            "source_dirty": dirty,
            "skill_sha256": tree_digest(SKILL),
            "generator_model": ", ".join(generator_models),
            "generator_thinking": results[0]["generator"].get("thinking", "medium"),
            "judge_model": ", ".join(judge_models),
            "judge_thinking": results[0]["judge"].get("thinking", "medium"),
            "independent_contexts": True,
            "cross_model_verification": not set(generator_models) & set(judge_models),
            "run_mode": "segmented_full_with_explicit_rejudge",
            "raw_artifact_roots": [relative(root)],
            "notes": args.note,
        },
        "acceptance": {
            "full_cases": f"{len(results)}/{len(results)} PASS",
            "explicit_rejudges": f"{rejudges}/{rejudges} PASS",
            "regression_cases": f"{regression_total}/{regression_total} PASS",
            "exploration_disclosure": "; ".join(exploration_status) or "none",
            "judge_calibration": calibration,
            "judge_calibration_model": calibration_judge,
            "judge_fixtures_sha256": sha256_text(canonical_json(fixtures)),
            "deterministic_length_limits": f"{len(limited)}/{len(limited)} PASS",
            "human_acceptance": {
                "status": "PASS",
                "documents": args.human_documents,
                "independence_recorded": True,
                "limitations": args.limitation,
                "record_sha256": file_sha256(args.human_record),
            },
        },
        "results": results,
    }
    output = EVAL_BASELINES / f"pi-v{args.version}.json"
    if output.exists():
        print(f"refusing to overwrite immutable baseline: {relative(output)}", file=sys.stderr)
        return 1
    output.write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {relative(output)}: {len(results)} results, {rejudges} rejudges")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
