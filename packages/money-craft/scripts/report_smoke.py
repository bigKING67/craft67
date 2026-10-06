#!/usr/bin/env python3
"""Render and verify a real acceptance report with the optional report runtime."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "money-craft" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import report_renderer  # noqa: E402


def smoke() -> dict[str, Any]:
    source = ROOT / "artifacts" / "acceptance" / "600519" / "report.md"
    evidence = ROOT / "artifacts" / "acceptance" / "600519" / "evidence-manifest.json"
    audit = ROOT / "artifacts" / "acceptance" / "600519" / "report-audit.json"
    try:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            output_html = output_dir / "report.html"
            output_pdf = output_dir / "report.pdf"
            render = report_renderer.render_report(
                source,
                output_html=output_html,
                output_pdf=output_pdf,
                evidence_manifest=evidence,
                audit_path=audit,
            )
            verification = report_renderer.verify_rendered_report(
                source,
                output_html,
                output_pdf,
            )
            if render.get("valid") is not True or verification.get("valid") is not True:
                raise report_renderer.ReportRenderError("report render verification failed")
            return {
                "schema": "money-craft.report-smoke.v1",
                "valid": True,
                "source": str(source.relative_to(ROOT)),
                "checks": [
                    "acceptance-report-render",
                    "portable-html-verify",
                    "pdf-structure-verify",
                ],
                "pages": verification["pages"],
                "charts": render["charts"],
                "placeholders": render["placeholders"],
                "external_dependencies": render["external_dependencies"],
                "network_used": render["network_used"],
                "errors": [],
            }
    except (OSError, UnicodeDecodeError, report_renderer.ReportRenderError) as exc:
        return {
            "schema": "money-craft.report-smoke.v1",
            "valid": False,
            "source": str(source.relative_to(ROOT)),
            "checks": [],
            "errors": [str(exc)],
        }


def main() -> int:
    payload = smoke()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
