#!/usr/bin/env python3
"""Replay the public two-filing fixture using privately stored original reports."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "money-craft" / "scripts"))
import earnings_update
import research_workflow
import tracking_workflow


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path, help="new directory; existing output is never overwritten")
    args = parser.parse_args()
    case = ROOT / "acceptance" / "earnings"
    previous = case / "600519-previous-thesis.md"
    current = case / "600519-current-thesis.md"
    payload = json.loads((case / "600519-2023-2024.json").read_text())
    result = earnings_update.build_update(payload, base=args.evidence_dir.resolve(), previous_thesis=previous)
    if not result["valid"]:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / "earnings-update.json").write_bytes(tracking_workflow.json_bytes(result))
    root = output / "tracking"
    initialized = tracking_workflow.initialize_tracking(root, as_of=result["as_of"], previous=previous,
                                                        template_root=ROOT / "skills" / "money-craft" / "templates")
    workspace = Path(initialized["workspace"])
    # This is the committed, explicitly reviewed historical candidate, not an
    # automatic inference of hypothesis support from positive financial deltas.
    candidate = research_workflow.load_thesis(current)
    for group, column in (("hypotheses", "状态"), ("red_lines", "当前状态")):
        actual = {r["ID"]: r[column] for r in candidate[group]}
        expected = {sid: r["status"] for sid, r in result["tracking_handoff"]["updates"][group].items()}
        if actual != expected:
            raise ValueError("reviewed candidate does not match earnings handoff")
    (workspace / "thesis.md").write_bytes(current.read_bytes())
    state = tracking_workflow.initial_state(candidate, as_of=result["as_of"], source_research=None)
    state["next_mandatory_review"] = {"event": "historical replay review window ends", "required_workflow": "earnings-review", "due_date": "2025-12-31"}
    (workspace / "state.json").write_bytes(tracking_workflow.json_bytes(state))
    (workspace / "card.md").write_text("# 历史工程回放\n两期正式年报数据与演示估值参数已复算。\n长期论文及红线仍为 UNVERIFIED；非买卖信号，非最新投资观点。\n", encoding="utf-8")
    sealed = tracking_workflow.finalize_tracking(workspace)
    verification = tracking_workflow.verify_tracking(root)
    status = tracking_workflow.tracking_status(root)
    receipt = {"schema": "money-craft.earnings-case-check.v1", "valid": verification["valid"],
               "input_sha256": earnings_update.digest(case / "600519-2023-2024.json"),
               "previous_thesis_sha256": earnings_update.digest(previous), "current_thesis_sha256": earnings_update.digest(current),
               "calculation_receipt_sha256": earnings_update.digest(output / "earnings-update.json"),
               "source_hashes": {sid: value["sha256"] for sid, value in payload["sources"].items()},
               "tracking_revision": sealed["tracking_revision"], "tracking_verify": verification,
               "current_assessment": status["assessment"], "historical_replay": True,
               "semantic_source_validation": "see manually reviewed acceptance/earnings/README.md; this command verifies file hashes",
               "network_used": False}
    (output / "acceptance-receipt.json").write_bytes(tracking_workflow.json_bytes(receipt))
    print(json.dumps({"valid": receipt["valid"], "output_dir": str(output), "tracking_revision": sealed["tracking_revision"],
                      "health_status": sealed["health_status"], "health_score": sealed["health_score"],
                      "current_assessment": status["assessment"]}, ensure_ascii=False, indent=2))
    return 0 if receipt["valid"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, research_workflow.WorkflowError, tracking_workflow.TrackingError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
