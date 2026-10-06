#!/usr/bin/env python3
"""Seal a dated, explicitly hypothetical forward case from two pinned public filings."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/money-craft/scripts"))
import earnings_baseline as baseline
import earnings_update as eu
import financial_rigor as finance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--half-year", required=True, type=Path)
    parser.add_argument("--prior-q3", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    specs = [
        ("S01", args.half_year, "2026 half-year report", "2026-08-15", "https://static.cninfo.com.cn/finalpage/2026-08-15/1225475868.PDF", "0e10aa26be46b1cf3cd03f06e834c7fb98d5dd0d661b96f8fddd4af7e846a4f6"),
        ("S02", args.prior_q3, "2025 Q3 report; conservative availability date from issuer upload path", "2025-11-02", "https://www.moutai.com.cn/mtgf/articleFileDir/2025-11/02/69eb1067f71f4d4da582a651eb580e0c.pdf", "622935d03b23310dcde1ba3c3d398b130c3fbf73b753fb79fab934999524307a")]
    sources = {}
    for sid, path, title, published, url, expected in specs:
        eu.require(path.is_file() and not path.is_symlink() and eu.digest(path) == expected, f"{sid}: pinned source mismatch")
        sources[sid] = {"security_id": "CN-SH:600519", "title": title, "url": url, "published_on": published,
                        "sha256": expected, "local_path": str(path.resolve())}
    refs = [{"source_id": "S01", "locator": "PDF p.5: H1 current and comparative columns"},
            {"source_id": "S02", "locator": "PDF p.1: standalone Q3 column, not YTD"}]
    expectations, calculations = [], []
    # Facts checked in the downloaded reports, not copied from a search snippet.
    for metric, current_h1, prior_h1, prior_q3 in [
            ("revenue", "90703260964.48", "89389354416.84", "39064353239.02"),
            ("net_income", "44516880421.86", "45402962298.10", "19223784414.08")]:
        ratio = finance.calculate("divide", [current_h1, prior_h1])
        q3 = finance.calculate("multiply", [prior_q3, ratio])
        ytd = finance.calculate("add", [current_h1, q3])
        for suffix, op, inputs, value in [("ratio", "divide", [current_h1, prior_h1], ratio),
                ("q3", "multiply", [prior_q3, str(ratio)], q3), ("ytd", "add", [current_h1, str(q3)], ytd)]:
            calculations.append({"id": f"C{len(calculations) + 1:02d}", "operation": op, "inputs": inputs, "expected": str(value), "tolerance": "0.000001"})
        expectations.append({"metric": metric, "origin": "analyst", "rationale": "HYPOTHESIZED mechanical continuity: 2026 H1 + 2025 standalone Q3 * (2026 H1 / 2025 H1). Not consensus or management guidance; no independent numeric cross-check.",
            "value": str(ytd), "unit": "CNY", "as_of": "2026-09-15", "period_start": "2026-01-01", "period_end": "2026-09-30",
            "kind": "ytd", "accounting_basis": "PRC-GAAP consolidated; net_income attributable to parent", "source_refs": refs})
    preview = {"schema": "money-craft.earnings-preview.v1", "security_id": "CN-SH:600519", "currency": "CNY", "as_of": "2026-09-15", "sources": sources,
        "expectations": expectations, "catalysts": [{"id": "C01", "window_start": "2026-10-01", "window_end": "2026-10-31",
        "impact_path": "Q3 sales and margin determine whether H1 trend continuity remains useful; window is an analyst watch window, not a confirmed disclosure appointment",
        "confirmation_condition": "Compare both actual YTD metrics to the separately saved forecasts after reconciling period and basis",
        "invalidation_condition": "Any material basis change or revenue/profit divergence requires revisiting the continuity assumption",
        "next_evidence": "Official 2026 Q3 filing, earliest actual-result disclosure, segment/channel mix and cash-flow explanation; seek independent numeric corroboration",
        "decision_condition": "Review assumption if either metric differs by more than 5 percent; this is an analyst review threshold, not a trading rule",
        "source_refs": refs}]}
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / "preview.json").write_text(json.dumps(preview, ensure_ascii=False, indent=2) + "\n")
    receipt = baseline.seal(output / "preview.json", output / "baseline.json")
    status = baseline.inspect_baseline(output / "baseline.json")
    note = "# Forward preview calculation acceptance\n\nAs of 2026-09-15; CN-SH:600519 ordinary A shares; CNY.\n\nHYPOTHESIZED engineering baseline, not an investment recommendation. Both filings are issuer-origin evidence; independent numeric corroboration is missing. Full research readiness is PARTIAL. No actual 2026 Q3 outcome is supplied.\n\n"
    for calc in calculations:
        note += "<!-- money-craft-calc: " + json.dumps(calc) + " -->\n\n"
    (output / "calculations.md").write_text(note)
    result = {"schema": "money-craft.forward-preview-case.v1", "valid": True, "seal": receipt, "inspection": status,
              "independent_numeric_crosscheck": "MISSING", "research_readiness": "PARTIAL", "actual_outcome": "NOT_PROVIDED",
              "source_hashes": {sid: s["sha256"] for sid, s in sources.items()}, "network_used": False}
    (output / "acceptance-receipt.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, eu.EarningsError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}))
        raise SystemExit(1)
