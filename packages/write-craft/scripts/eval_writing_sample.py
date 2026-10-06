#!/usr/bin/env python3
"""Generate one frozen, first-draft writing sample. Development only.

Run separately for each Skill snapshot with identical cases/model/settings.
The existing fact evaluator is reused; its PASS is not an editorial verdict.
Never overwrite an earlier sample or silently revise a held-out draft.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts import eval_behavior as behavior
except ModuleNotFoundError:
    import eval_behavior as behavior


def first_draft_cases(path: Path) -> list[dict]:
    cases = behavior.load_cases(path)
    if any(case.get("max_revisions", 0) != 0 for case in cases):
        raise behavior.ContractError("writing samples require max_revisions=0")
    if any("reader_test" in case for case in cases):
        raise behavior.ContractError("first-draft comparison keeps reader testing separate")
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--judge-model", required=True)
    parser.add_argument("--thinking", default="low")
    parser.add_argument("--judge-thinking", help="defaults to --thinking")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    judge_thinking = args.judge_thinking or args.thinking
    skill = args.skill.resolve()
    if not (skill / "SKILL.md").is_file() or args.timeout < 1:
        parser.error("an existing Skill and a positive timeout are required")
    cases = first_draft_cases(args.cases.resolve())
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    behavior.SKILL_ROOT = skill
    digest = behavior.skill_digest(skill)
    manifest = {
        "skill_digest": digest,
        "cases_digest": behavior.sha256_text(args.cases.read_text()),
        "model": args.model,
        "judge_model": args.judge_model,
        "thinking": args.thinking,
        "judge_thinking": judge_thinking,
        "pi_version": behavior.pi_version(),
        "started_at": behavior.utc_now(),
        "evaluator_digest": behavior.sha256_text(Path(behavior.__file__).read_text()),
        "runner_digest": behavior.sha256_text(Path(__file__).read_text()),
        "runs_per_case": 1,
        "max_revisions": 0,
        "raw_jsonl": False,
        "results": [],
        "editorial_acceptance": "NOT_EVALUATED",
        "human_acceptance": "NOT_RUN",
    }
    behavior.write_json(output / "sample.json", manifest)
    consecutive_errors = 0
    for case in cases:
        if behavior.skill_digest(skill) != digest:
            raise behavior.ContractError("Skill changed during sample generation")
        result = behavior.evaluate_case(
            case=case, run_index=1, output_root=output,
            model=args.model, judge_model=args.judge_model,
            reader_model=args.judge_model, reader_judge_model=args.judge_model,
            thinking=args.thinking, judge_thinking=judge_thinking,
            reader_thinking=judge_thinking, reader_judge_thinking=judge_thinking,
            timeout=args.timeout,
        )
        manifest["results"].append(result)
        behavior.write_json(output / "sample.json", manifest)
        print(json.dumps({"case": case["id"], "status": result["status"],
                          "editorial": result.get("editorial", {}).get("status")}), flush=True)
        consecutive_errors = consecutive_errors + 1 if result["status"] == "ERROR" else 0
        if consecutive_errors >= 3:
            break
    manifest["finished_at"] = behavior.utc_now()
    manifest["snapshot_unchanged"] = behavior.skill_digest(skill) == digest
    manifest["not_run"] = [case["id"] for case in cases[len(manifest["results"]):]]
    manifest["fact_contract_status"] = (
        "PASS" if not manifest["not_run"] and manifest["snapshot_unchanged"]
        and all(result["status"] == "PASS" for result in manifest["results"])
        else "INCOMPLETE_OR_FAILED"
    )
    behavior.write_json(output / "sample.json", manifest)
    return 0 if manifest["fact_contract_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
