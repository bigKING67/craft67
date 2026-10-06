#!/usr/bin/env python3
"""Create or validate bounded measurement-only screenshot comparisons."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
LIB_DIR = SCRIPT_DIR.parent / "lib"
sys.dont_write_bytecode = True
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from design_craft.comp_fidelity import (  # noqa: E402
    CompFidelityError,
    PngImage,
    compare,
    validate_report,
    write_png,
)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--check", action="store_true", help="Run a dependency-free self-check")
    commands = root.add_subparsers(dest="command")
    create = commands.add_parser("compare")
    create.add_argument("--reference", required=True)
    create.add_argument("--rendered", required=True)
    create.add_argument("--spec", required=True)
    create.add_argument("--output-dir", required=True)
    create.add_argument("--observed-at")
    validate = commands.add_parser("validate")
    validate.add_argument("--manifest", required=True)
    validate.add_argument("--reference")
    validate.add_argument("--rendered")
    validate.add_argument("--spec")
    validate.add_argument("--strict", action="store_true")
    return root


def self_check() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="design-craft-comp-check-") as raw:
        root = Path(raw)
        reference = root / "reference.png"
        rendered = root / "rendered.png"
        spec = root / "spec.json"
        write_png(reference, PngImage(2, 1, bytes((0, 0, 0, 255, 255, 255, 255, 255))))
        write_png(rendered, PngImage(2, 1, bytes((0, 0, 0, 255, 224, 224, 224, 255))))
        spec.write_text(
            json.dumps({
                "schema": "design-craft.comp-fidelity-spec.v1",
                "case_id": "self-check",
                "coordinate_space": {"width": 2, "height": 1},
                "changed_pixel_delta": 0.01,
                "regions": [{"id": "canvas", "box": [0, 0, 2, 1], "salience": "primary", "dimensions": ["geometry", "type"], "note": "self-check canvas"}],
            }),
            encoding="utf-8",
        )
        output = root / "result"
        report = compare(reference_path=reference, rendered_path=rendered, spec_path=spec, output_dir=output, observed_at="2026-01-01T00:00:00Z")
        validation = validate_report(output / "report.json", reference_path=reference, rendered_path=rendered, spec_path=spec, strict=True)
        return {"schema": "design-craft.comp-fidelity-self-check.v1", "ok": validation["ok"], "verdict": report["verdict"], "artifact_count": validation["artifact_count"]}


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.check:
            payload = self_check()
        elif args.command == "compare":
            payload = compare(
                reference_path=Path(args.reference),
                rendered_path=Path(args.rendered),
                spec_path=Path(args.spec),
                output_dir=Path(args.output_dir),
                observed_at=args.observed_at,
            )
        elif args.command == "validate":
            payload = validate_report(
                Path(args.manifest),
                reference_path=Path(args.reference) if args.reference else None,
                rendered_path=Path(args.rendered) if args.rendered else None,
                spec_path=Path(args.spec) if args.spec else None,
                strict=args.strict,
            )
        else:
            parser().print_help(sys.stderr)
            return 2
    except (CompFidelityError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
