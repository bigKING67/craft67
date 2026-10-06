#!/usr/bin/env python3
"""Prepare, close out, and validate hash-bound sealed-rendition evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
LIB_DIR = SCRIPT_DIR.parent / "lib"
sys.dont_write_bytecode = True
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from design_craft.comp_fidelity import PngImage, write_png  # noqa: E402
from design_craft.sealed_rendition import (  # noqa: E402
    REPORT_SCHEMA,
    SPEC_SCHEMA,
    SealedRenditionError,
    closeout_gate,
    prepare_gate,
    validate_gate_report,
)
from design_craft_shadow_lab import ShadowLabError, verify_lab  # noqa: E402


def _json_text(payload: dict[str, object], *, pretty: bool = False) -> str:
    """Serialize machine output without depending on the console code page."""

    return json.dumps(
        payload,
        ensure_ascii=True,
        indent=2 if pretty else None,
        sort_keys=pretty,
    )


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--check", action="store_true", help="Run a dependency-free self-check")
    commands = root.add_subparsers(dest="command")

    prepare = commands.add_parser("prepare")
    prepare.add_argument("--spec", required=True)
    prepare.add_argument("--output-root", required=True)
    prepare.add_argument("--prepared-at")

    closeout = commands.add_parser("closeout")
    closeout.add_argument("--plan", required=True)
    closeout.add_argument(
        "--visual-decision",
        required=True,
        choices=("pending", "pass", "blocked", "incomplete"),
    )
    closeout.add_argument("--visual-note", required=True)
    closeout.add_argument("--reviewer")
    closeout.add_argument("--observed-at")

    validate = commands.add_parser("validate")
    validate.add_argument("--report", required=True)
    validate.add_argument("--strict", action="store_true")
    return root


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def self_check() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="design-craft-sealed-gate-check-") as raw:
        root = Path(raw)
        sealed = root / "sealed source with spaces"
        sealed.mkdir()
        source = sealed / "page.html"
        reference = sealed / "reference.png"
        source.write_bytes(b"<!doctype html>\r\n<title>sealed</title>\x1a")
        write_png(reference, PngImage(2, 1, bytes((12, 24, 36, 255)) * 2))
        files = [
            {"path": path.name, "bytes": path.stat().st_size, "sha256": _sha256(path)}
            for path in (source, reference)
        ]
        manifest = sealed / "manifest.json"
        manifest.write_text(
            json.dumps({"schema": "self-check.sealed.v1", "files": files}),
            encoding="utf-8",
        )
        comparison_spec = root / "comparison.json"
        comparison_spec.write_text(
            json.dumps(
                {
                    "schema": "design-craft.comp-fidelity-spec.v1",
                    "case_id": "sealed-self-check",
                    "coordinate_space": {"width": 2, "height": 1},
                    "changed_pixel_delta": 0.01,
                    "regions": [
                        {
                            "id": "canvas",
                            "box": [0, 0, 2, 1],
                            "salience": "primary",
                            "dimensions": ["content"],
                            "note": "self-check canvas",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        gate_spec = root / "gate.json"
        gate_spec.write_text(
            json.dumps(
                {
                    "schema": SPEC_SCHEMA,
                    "gate_id": "sealed-self-check",
                    "authority": {
                        "kind": "sealed_manifest",
                        "root": str(sealed),
                        "manifest": str(manifest),
                        "expected_schema": "self-check.sealed.v1",
                        "inventory_key": "files",
                        "anchors": [],
                    },
                    "captures": [
                        {
                            "id": "desktop",
                            "kind": "browser_viewport",
                            "source": "page.html",
                            "reference": "reference.png",
                            "comparison_spec": str(comparison_spec),
                            "contract": {
                                "runtime": "browser67",
                                "viewport": {"width": 2, "height": 1},
                                "device_scale_factor": 1,
                                "theme": "light",
                                "network": "offline",
                                "wait_for": "document_complete",
                            },
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        output = root / "evidence"
        plan = prepare_gate(
            spec_path=gate_spec,
            output_root=output,
            shadow_lab_verifier=verify_lab,
            prepared_at="2026-01-01T00:00:00Z",
        )
        shutil.copyfile(reference, Path(plan["captures"][0]["rendered_path"]))
        report = closeout_gate(
            plan_path=output / "capture-plan.json",
            visual_decision="pending",
            visual_note="Self-check intentionally leaves visual acceptance pending.",
            shadow_lab_verifier=verify_lab,
            observed_at="2026-01-01T00:00:01Z",
        )
        validation = validate_gate_report(
            output / "gate-report.json",
            strict=True,
            shadow_lab_verifier=verify_lab,
        )
        return {
            "schema": "design-craft.sealed-rendition-gate-self-check.v1",
            "ok": validation["ok"],
            "report_schema": report["schema"],
            "capture_count": validation["capture_count"],
            "visual_decision": validation["visual_decision"],
            "global_pixel_pass_threshold": validation["global_pixel_pass_threshold"],
        }


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.check:
            payload = self_check()
        elif args.command == "prepare":
            payload = prepare_gate(
                spec_path=Path(args.spec),
                output_root=Path(args.output_root),
                shadow_lab_verifier=verify_lab,
                prepared_at=args.prepared_at,
            )
        elif args.command == "closeout":
            payload = closeout_gate(
                plan_path=Path(args.plan),
                visual_decision=args.visual_decision,
                visual_note=args.visual_note,
                reviewer=args.reviewer,
                shadow_lab_verifier=verify_lab,
                observed_at=args.observed_at,
            )
        elif args.command == "validate":
            payload = validate_gate_report(
                Path(args.report),
                strict=args.strict,
                shadow_lab_verifier=verify_lab,
            )
        else:
            parser().print_help(sys.stderr)
            return 2
    except (SealedRenditionError, ShadowLabError, OSError, ValueError) as exc:
        print(_json_text({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 2
    if payload.get("schema") not in {
        REPORT_SCHEMA,
        "design-craft.sealed-rendition-capture-plan.v1",
        "design-craft.sealed-rendition-gate-validation.v1",
        "design-craft.sealed-rendition-gate-self-check.v1",
    }:
        print(_json_text({"ok": False, "error": "unexpected output schema"}), file=sys.stderr)
        return 2
    print(_json_text(payload, pretty=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
