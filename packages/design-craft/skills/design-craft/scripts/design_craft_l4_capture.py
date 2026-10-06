#!/usr/bin/env python3
"""Capture generic L4 before/after screenshot evidence manifests.

This is the deterministic fallback path for L4 evals when an interactive MCP
browser bundle helper is unavailable. Prefer TMWD bundle capture when the host
exposes it; use this wrapper to keep the Chrome-headless fallback repeatable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from design_craft_l4_evidence_manifest import SCHEMA, validate_manifest  # noqa: E402


CAPTURE_PLAN_SCHEMA = "design-craft.l4-capture-plan.v1"
DEFAULT_VIEWPORTS = ("desktop=1440x900", "compact500=500x844")
VIEWPORT_PATTERN = re.compile(
    r"^(?:(?P<name>[A-Za-z0-9._-]+)=)?(?P<width>[1-9][0-9]*)x(?P<height>[1-9][0-9]*)(?:@(?P<dpr>[0-9]+(?:\.[0-9]+)?))?$"
)
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@dataclass(frozen=True)
class Viewport:
    key: str
    width: int
    height: int
    dpr: float

    @property
    def is_mobile(self) -> bool:
        return self.width <= 700

    @property
    def css_size(self) -> str:
        return f"{self.width}x{self.height}"


def parse_viewport(spec: str) -> Viewport:
    match = VIEWPORT_PATTERN.fullmatch(spec)
    if not match:
        raise ValueError(
            f"Invalid viewport {spec!r}; use name=WIDTHxHEIGHT or name=WIDTHxHEIGHT@DPR"
        )
    width = int(match.group("width"))
    height = int(match.group("height"))
    dpr = float(match.group("dpr") or 1)
    if dpr <= 0:
        raise ValueError(f"Invalid viewport {spec!r}; DPR must be positive")
    key = match.group("name") or f"{width}x{height}"
    return Viewport(key=key, width=width, height=height, dpr=dpr)


def parse_viewports(specs: list[str]) -> list[Viewport]:
    seen: set[str] = set()
    viewports: list[Viewport] = []
    for spec in specs:
        viewport = parse_viewport(spec)
        if viewport.key in seen:
            raise ValueError(f"Duplicate viewport key: {viewport.key}")
        seen.add(viewport.key)
        viewports.append(viewport)
    return viewports


def sanitize_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return slug or "capture"


def default_artifact_root(case_id: str) -> Path:
    base = os.environ.get("DESIGN_CRAFT_ARTIFACT_ROOT")
    if base:
        root = Path(base).expanduser()
    else:
        root = Path.home() / ".tmwd-browser-mcp" / "runtime" / "runs"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return root / sanitize_slug(case_id) / f"{stamp}-chrome-headless-fallback" / "artifacts"


def find_chrome(explicit: str | None) -> str:
    if explicit:
        if Path(explicit).expanduser().exists():
            return str(Path(explicit).expanduser())
        found = shutil.which(explicit)
        if found:
            return found
        raise FileNotFoundError(f"Chrome binary not found: {explicit}")

    candidates = [
        os.environ.get("CHROME_BIN"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "chrome",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        candidate_path = Path(candidate).expanduser()
        if candidate_path.exists():
            return str(candidate_path)
        found = shutil.which(candidate)
        if found:
            return found
    raise FileNotFoundError("Chrome binary not found. Set CHROME_BIN or pass --chrome-bin.")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def png_dimensions(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if len(header) < 24 or not header.startswith(PNG_SIGNATURE) or header[12:16] != b"IHDR":
        raise ValueError(f"{path} is not a PNG screenshot with an IHDR header")
    width, height = struct.unpack(">II", header[16:24])
    if width <= 0 or height <= 0:
        raise ValueError(f"{path} has invalid PNG dimensions: {width}x{height}")
    return width, height


def chrome_command(chrome: str, url: str, output_path: Path, viewport: Viewport) -> list[str]:
    dpr = int(viewport.dpr) if viewport.dpr.is_integer() else viewport.dpr
    return [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-first-run",
        "--disable-background-networking",
        "--run-all-compositor-stages-before-draw",
        f"--force-device-scale-factor={dpr}",
        f"--window-size={viewport.width},{viewport.height}",
        f"--screenshot={output_path}",
        url,
    ]


def capture_chrome(
    *,
    chrome: str,
    url: str,
    output_path: Path,
    viewport: Viewport,
    timeout_sec: int,
    strict_exit_code: bool,
) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        chrome_command(chrome, url, output_path, viewport),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout_sec,
        check=False,
    )
    if strict_exit_code and result.returncode != 0:
        raise RuntimeError(
            f"Chrome exited {result.returncode} for {url} at {viewport.key}; "
            f"stderr tail: {result.stderr[-800:]}"
        )
    if not output_path.is_file():
        raise RuntimeError(
            f"Chrome did not write screenshot {output_path} for {url} at {viewport.key}; "
            f"exit={result.returncode}; stderr tail: {result.stderr[-800:]}"
        )

    width, height = png_dimensions(output_path)
    artifact: dict[str, Any] = {
        "tool": "google-chrome-headless-cli",
        "target": "viewport",
        "path": str(output_path),
        "sha256": file_sha256(output_path),
        "dimensions": [width, height],
        "viewport": {
            "width": viewport.width,
            "height": viewport.height,
            "dpr": viewport.dpr,
            "is_mobile": viewport.is_mobile,
        },
        "capture": {
            "requested_viewport": [viewport.width, viewport.height],
            "requested_dpr": viewport.dpr,
            "chrome_exit_code": result.returncode,
            "nonfatal_stderr": bool(result.stderr.strip()),
        },
    }
    if result.returncode != 0:
        artifact["capture"]["nonfatal_reason"] = "artifact existed and PNG metadata verified"
    return artifact


def build_plan_payload(
    *,
    case_id: str,
    before_url: str,
    after_url: str,
    artifact_root: Path,
    viewports: list[Viewport],
) -> dict[str, Any]:
    return {
        "schema": CAPTURE_PLAN_SCHEMA,
        "case_id": case_id,
        "preferred_tool": "tmwd_browser.browser_evidence_bundle_ops",
        "fallback_tool": "google-chrome-headless-cli",
        "artifact_root": str(artifact_root),
        "phases": {
            "before": {"url": before_url},
            "after": {"url": after_url},
        },
        "viewports": [
            {
                "key": viewport.key,
                "width": viewport.width,
                "height": viewport.height,
                "dpr": viewport.dpr,
                "is_mobile": viewport.is_mobile,
            }
            for viewport in viewports
        ],
        "notes": [
            "Prefer the TMWD evidence bundle helper when the active agent exposes it.",
            "Use the Chrome fallback only when MCP screenshot capture is unavailable or for offline local fixtures.",
            "Store PNG artifacts outside the repository and commit only screenshots.json metadata.",
            "Run design_craft_l4_evidence_manifest.py with --strict after capture.",
        ],
    }


def build_manifest(
    *,
    case_id: str,
    before_url: str,
    after_url: str,
    artifact_root: Path,
    artifacts: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    shared_keys = sorted(set(artifacts["before"]) & set(artifacts["after"]))
    layout_delta: dict[str, Any] = {}
    for key in shared_keys:
        before = artifacts["before"][key]
        after = artifacts["after"][key]
        layout_delta[key] = {
            "before_dimensions": before.get("dimensions"),
            "after_dimensions": after.get("dimensions"),
            "requested_viewport": before.get("capture", {}).get("requested_viewport"),
            "horizontal_overflow": "not measured by Chrome-headless fallback",
        }

    return {
        "schema": SCHEMA,
        "case_id": case_id,
        "route": after_url if before_url == after_url else "before_url and after_url",
        "capture_context": {
            "artifact_root": str(artifact_root),
            "capture_tool": "Google Chrome headless CLI fallback",
            "preferred_tool": "tmwd_browser.browser_evidence_bundle_ops",
            "fallback_reason": "Use when MCP screenshot capture is unavailable or a deterministic local fixture is enough.",
            "before_url": before_url,
            "after_url": after_url,
            "notes": [
                "PNG artifacts are repo-external; commit only metadata.",
                "If TMWD becomes available later, run bundle verification against these paths before citing the case.",
                "This fallback records viewport screenshots and PNG metadata; interaction states require separate evidence.",
            ],
        },
        "artifacts": artifacts,
        "layout_delta": layout_delta,
    }


def run_capture(args: argparse.Namespace) -> dict[str, Any]:
    viewports = parse_viewports(args.viewport or list(DEFAULT_VIEWPORTS))
    artifact_root = Path(args.artifact_root).expanduser() if args.artifact_root else default_artifact_root(args.case_id)
    if args.dry_run:
        return build_plan_payload(
            case_id=args.case_id,
            before_url=args.before_url,
            after_url=args.after_url,
            artifact_root=artifact_root,
            viewports=viewports,
        )

    chrome = find_chrome(args.chrome_bin)
    artifacts: dict[str, dict[str, dict[str, Any]]] = {"before": {}, "after": {}}
    for phase, url in (("before", args.before_url), ("after", args.after_url)):
        for viewport in viewports:
            filename = (
                f"screenshot-viewport-{sanitize_slug(args.case_id)}-"
                f"{phase}-{sanitize_slug(viewport.key)}-chrome-headless.png"
            )
            artifacts[phase][viewport.key] = capture_chrome(
                chrome=chrome,
                url=url,
                output_path=artifact_root / filename,
                viewport=viewport,
                timeout_sec=args.timeout_sec,
                strict_exit_code=args.strict_exit_code,
            )
    return build_manifest(
        case_id=args.case_id,
        before_url=args.before_url,
        after_url=args.after_url,
        artifact_root=artifact_root,
        artifacts=artifacts,
    )


def write_payload(path: Path | None, payload: dict[str, Any]) -> None:
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if path is None:
        print(text, end="")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def run_self_check() -> list[str]:
    errors: list[str] = []
    try:
        parsed = parse_viewports(["desktop=1440x900", "phone=390x844@2"])
        if parsed[1].key != "phone" or parsed[1].dpr != 2:
            errors.append("self-check failed to parse viewport DPR")
    except Exception as exc:
        errors.append(f"self-check failed to parse valid viewports: {exc}")
    try:
        parse_viewport("bad")
        errors.append("self-check failed to reject malformed viewport")
    except ValueError:
        pass

    temp_root = Path(tempfile.mkdtemp(prefix="design-craft-l4-capture-"))
    try:
        fake_png = temp_root / "one-by-one.png"
        fake_png.write_bytes(PNG_SIGNATURE + b"\x00\x00\x00\rIHDR" + struct.pack(">II", 1, 1))
        if png_dimensions(fake_png) != (1, 1):
            errors.append("self-check failed to read PNG dimensions")
        digest = file_sha256(fake_png)
        artifact = {
            "tool": "google-chrome-headless-cli",
            "target": "viewport",
            "path": str(fake_png),
            "sha256": digest,
            "dimensions": [1, 1],
            "viewport": {"width": 1, "height": 1, "dpr": 1, "is_mobile": True},
        }
        manifest = build_manifest(
            case_id="generic-l4-capture-self-check",
            before_url="http://127.0.0.1:4173/before",
            after_url="http://127.0.0.1:4173/after",
            artifact_root=temp_root,
            artifacts={"before": {"desktop": artifact}, "after": {"desktop": artifact}},
        )
        manifest_path = temp_root / "screenshots.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        errors.extend(validate_manifest(manifest_path, strict=True, require_existing_files=True))
        plan = build_plan_payload(
            case_id="generic-l4-capture-self-check",
            before_url="http://127.0.0.1:4173/before",
            after_url="http://127.0.0.1:4173/after",
            artifact_root=temp_root,
            viewports=[Viewport(key="desktop", width=1440, height=900, dpr=1)],
        )
        if plan.get("preferred_tool") != "tmwd_browser.browser_evidence_bundle_ops":
            errors.append("self-check failed to keep TMWD bundle helper as preferred tool")
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture project-neutral L4 before/after screenshot evidence with a Chrome-headless fallback."
    )
    parser.add_argument("--check", action="store_true", help="Run self-checks without launching Chrome.")
    parser.add_argument("--case-id", help="Filesystem-safe L4 case id.")
    parser.add_argument("--before-url", help="Before-state URL to capture.")
    parser.add_argument("--after-url", help="After-state URL to capture.")
    parser.add_argument(
        "--viewport",
        action="append",
        help="Viewport spec name=WIDTHxHEIGHT or name=WIDTHxHEIGHT@DPR. Defaults to desktop and compact500.",
    )
    parser.add_argument("--artifact-root", help="Repo-external directory for PNG artifacts.")
    parser.add_argument("--manifest", help="Path to write screenshots.json. Defaults to stdout.")
    parser.add_argument("--chrome-bin", help="Chrome binary path or command. Defaults to CHROME_BIN or common names.")
    parser.add_argument("--timeout-sec", type=int, default=45, help="Per-screenshot Chrome timeout.")
    parser.add_argument("--strict-exit-code", action="store_true", help="Fail if Chrome exits non-zero even when PNG exists.")
    parser.add_argument("--dry-run", action="store_true", help="Print a TMWD-first capture plan without writing artifacts.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.check:
        errors = run_self_check()
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 1
        return 0

    missing = [name for name in ("case_id", "before_url", "after_url") if not getattr(args, name)]
    if missing:
        parser.error("Missing required arguments: " + ", ".join(f"--{name.replace('_', '-')}" for name in missing))
    if args.timeout_sec <= 0:
        parser.error("--timeout-sec must be positive")

    try:
        payload = run_capture(args)
        manifest_path = Path(args.manifest).expanduser() if args.manifest else None
        write_payload(manifest_path, payload)
        if not args.dry_run and manifest_path is not None:
            errors = validate_manifest(manifest_path, strict=True, require_existing_files=True)
            if errors:
                print("\n".join(errors), file=sys.stderr)
                return 1
    except Exception as exc:
        print(f"design_craft_l4_capture.py: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
