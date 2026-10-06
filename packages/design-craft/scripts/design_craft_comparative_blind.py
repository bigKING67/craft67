#!/usr/bin/env python3
"""Create an anonymized judging packet bound to comparative outputs and runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

from design_craft_comparative_common import (
    BLIND_LABELS,
    BLIND_MAP_SCHEMA,
    RUN_SCHEMA,
    SOURCE_BRAND_PATTERN,
    VARIANTS_SCHEMA,
    load_scorecard,
    sha256_file,
    render_scorecard_markdown,
    validate_judgment_schema,
    variant_ids,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-dir", required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    case_dir = Path(args.case_dir).expanduser().resolve()
    packet_path = case_dir / "blind-packet.md"
    map_path = case_dir / "blind-map.json"
    if not args.force and (packet_path.exists() or map_path.exists()):
        parser.error("refusing to overwrite blind packet/map without --force")

    weights, scorecard_errors = load_scorecard(case_dir)
    schema_errors = validate_judgment_schema(case_dir, weights) if weights else []
    if scorecard_errors or schema_errors:
        parser.error("; ".join([*scorecard_errors, *schema_errors]))
    try:
        rendered_scorecard = render_scorecard_markdown(case_dir)
        stored_scorecard = (case_dir / "scorecard.md").read_text(encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(f"cannot verify scorecard.md parity: {exc}")
    if stored_scorecard != rendered_scorecard:
        parser.error("scorecard.md must be generated exactly from scorecard.json")
    try:
        variants_payload = json.loads(
            (case_dir / "variants.json").read_text(encoding="utf-8")
        )
        if variants_payload.get("schema") != VARIANTS_SCHEMA:
            parser.error(f"variants.json must use {VARIANTS_SCHEMA}")
        required_variants = variant_ids(variants_payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(f"invalid variants.json: {exc}")
    for variant in required_variants:
        output_path = case_dir / f"output.{variant}.md"
        run_path = case_dir / f"run.{variant}.json"
        if not output_path.is_file() or not run_path.is_file():
            parser.error(f"missing observed output/run for {variant}")
        try:
            run_payload = json.loads(run_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            parser.error(f"invalid run manifest for {variant}: {exc}")
        if run_payload.get("schema") != RUN_SCHEMA:
            parser.error(f"run.{variant}.json must use {RUN_SCHEMA}")
        output_text = output_path.read_text(encoding="utf-8")
        match = SOURCE_BRAND_PATTERN.search(output_text)
        if match:
            parser.error(
                f"output.{variant}.md reveals a skill/source brand near {match.group(0)!r}"
            )

    shuffled = list(required_variants)
    random.Random(args.seed).shuffle(shuffled)
    mapping = dict(zip(BLIND_LABELS, shuffled, strict=True))
    prompt = (case_dir / "prompt.md").read_text(encoding="utf-8")
    scorecard_json = (case_dir / "scorecard.json").read_text(encoding="utf-8")
    judgment_schema = (case_dir / "judgment.schema.json").read_text(encoding="utf-8")
    sections = [
        "# Blind comparative judgment\n",
        "Judge only the supplied outputs. Do not infer which skill produced a label. ",
        "Apply the machine-readable scorecard exactly, recompute each total from ",
        "criterion points, and return only JSON matching the supplied schema.\n\n",
        "## Task prompt\n\n",
        prompt,
        "\n\n## Human-readable scorecard\n\n",
        rendered_scorecard,
        "\n\n## Machine-readable scorecard\n\n```json\n",
        scorecard_json.rstrip(),
        "\n```\n\n## Required judgment schema\n\n```json\n",
        judgment_schema.rstrip(),
        "\n```",
    ]
    outputs: dict[str, dict[str, str]] = {}
    for label, variant in mapping.items():
        output_path = case_dir / f"output.{variant}.md"
        run_path = case_dir / f"run.{variant}.json"
        outputs[label] = {
            "variant": variant,
            "path": output_path.name,
            "sha256": sha256_file(output_path),
            "run_path": run_path.name,
            "run_sha256": sha256_file(run_path),
        }
        sections.extend(
            (f"\n\n## Output {label}\n\n", output_path.read_text(encoding="utf-8"))
        )
    packet_path.write_text("".join(sections).rstrip() + "\n", encoding="utf-8")
    payload = {
        "schema": BLIND_MAP_SCHEMA,
        "case_id": case_dir.name,
        "focused_variant": variants_payload["focused_variant"],
        "seed_sha256": hashlib.sha256(args.seed.encode("utf-8")).hexdigest(),
        "prompt_sha256": sha256_file(case_dir / "prompt.md"),
        "scorecard_sha256": sha256_file(case_dir / "scorecard.md"),
        "scorecard_json_sha256": sha256_file(case_dir / "scorecard.json"),
        "judgment_schema_sha256": sha256_file(case_dir / "judgment.schema.json"),
        "packet_path": packet_path.name,
        "packet_sha256": sha256_file(packet_path),
        "outputs": outputs,
    }
    map_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(packet_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
