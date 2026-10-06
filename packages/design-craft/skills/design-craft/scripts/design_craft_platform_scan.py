#!/usr/bin/env python3
"""Infer a design target platform and run conservative native source checks."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
LIB_DIR = SCRIPT_DIR.parent / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from design_craft.authority import (
    ProjectMetadataError,
    project_root_for,
    read_owned_text,
    resolve_project_authority,
)


SCHEMA = "design-craft.platform-scan.v1"
PLATFORMS = {"auto", "web", "ios", "android", "adaptive"}
IGNORED_DIRS = {
    ".git",
    ".gradle",
    ".idea",
    ".next",
    ".swiftpm",
    ".turbo",
    ".venv",
    "Pods",
    "build",
    "coverage",
    "dist",
    "DerivedData",
    "node_modules",
    "upstreams",
    "vendor",
}
TEXT_SUFFIXES = {
    ".css",
    ".dart",
    ".gradle",
    ".html",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".kt",
    ".kts",
    ".m",
    ".md",
    ".mm",
    ".swift",
    ".toml",
    ".ts",
    ".tsx",
    ".vue",
    ".xml",
    ".yaml",
    ".yml",
}


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    platform: str
    path: str
    line: int
    message: str


def resolve_target(raw: str) -> Path:
    target = Path(raw).expanduser().resolve()
    return target.parent if target.is_file() else target


def walk_files(root: Path, *, max_files: int = 20000) -> Iterable[Path]:
    count = 0
    for current, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name not in IGNORED_DIRS and not name.startswith(".")]
        for name in files:
            path = Path(current) / name
            if path.suffix.lower() not in TEXT_SUFFIXES and name not in {
                "Podfile",
                "Package.swift",
                "pubspec.yaml",
                "settings.gradle",
                "settings.gradle.kts",
            }:
                continue
            yield path
            count += 1
            if count >= max_files:
                return


def read_text(path: Path, limit: int = 1_000_000) -> str:
    try:
        if path.stat().st_size > limit:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def discover_product_context(target: Path, explicit: str) -> tuple[Path | None, str]:
    resolution = resolve_project_authority(
        target,
        "PRODUCT.md",
        explicit=explicit or None,
    )
    return resolution.path, resolution.source


def parse_product_platform(path: Path | None) -> tuple[str | None, list[str]]:
    if path is None or not path.is_file():
        return None, []
    lines = read_text(path).splitlines()
    signals: list[str] = []
    for index, raw in enumerate(lines):
        line = raw.strip()
        inline = re.match(r"^(?:[-*]\s*)?platform\s*:\s*([A-Za-z-]+)\s*$", line, re.I)
        if inline:
            value = inline.group(1).lower()
            signals.append(f"PRODUCT.md inline Platform={value}")
            return (value if value in PLATFORMS - {"auto"} else None), signals
        if re.match(r"^#{2,6}\s+platform\s*$", line, re.I):
            for candidate in lines[index + 1 : index + 8]:
                value = candidate.strip().lstrip("-* ").strip("` ").lower()
                if not value:
                    continue
                value = value.split()[0].strip("`:;,.")
                signals.append(f"PRODUCT.md Platform={value}")
                return (value if value in PLATFORMS - {"auto"} else None), signals
    return None, signals


def package_dependencies(target: Path) -> tuple[set[str], str | None]:
    boundary = project_root_for(target)
    for directory in (target, *target.parents):
        candidate = directory / "package.json"
        if os.path.lexists(candidate):
            try:
                raw = read_owned_text(candidate, boundary, label="package.json")
                payload = json.loads(raw)
            except (ProjectMetadataError, json.JSONDecodeError) as exc:
                return set(), f"package metadata unavailable: {exc}"
            if not isinstance(payload, dict):
                return set(), "package metadata unavailable: package.json must contain an object"
            names: set[str] = set()
            for key in ("dependencies", "devDependencies", "peerDependencies"):
                values = payload.get(key)
                if isinstance(values, dict):
                    names.update(str(name).lower() for name in values)
            return names, None
        if directory == boundary:
            return set(), None
    return set(), None


def has_any(target: Path, candidates: Iterable[str]) -> bool:
    return any((target / candidate).exists() for candidate in candidates)


def codebase_platform(target: Path) -> tuple[str, float, list[str]]:
    deps, metadata_issue = package_dependencies(target)
    signals: list[str] = []
    if metadata_issue:
        signals.append(metadata_issue)

    web_shell = any(
        name.startswith("@capacitor/")
        or name.startswith("cordova-")
        or name in {"@ionic-native/core", "cordova", "capacitor"}
        for name in deps
    )
    react_native = "react-native" in deps or "expo" in deps
    flutter = (target / "pubspec.yaml").is_file() and "flutter:" in read_text(target / "pubspec.yaml")
    kmp_files = [target / "settings.gradle.kts", target / "build.gradle.kts", target / "composeApp/build.gradle.kts"]
    kmp = any(
        path.is_file()
        and re.search(r"kotlin\s*\(\s*[\"']multiplatform|org\.jetbrains\.kotlin\.multiplatform", read_text(path))
        for path in kmp_files
    )

    ios_markers = has_any(
        target,
        ["ios", "iOS", "Package.swift"],
    ) or any(target.glob("*.xcodeproj")) or any(target.glob("*.xcworkspace"))
    android_markers = has_any(
        target,
        ["android", "app/src/main/AndroidManifest.xml", "settings.gradle", "settings.gradle.kts"],
    )

    if web_shell:
        signals.append("Capacitor/Cordova/WebView shell dependency keeps the UI platform web")
        return "web", 0.9, signals
    if react_native:
        signals.append("React Native/Expo dependency")
        return "adaptive", 0.92, signals
    if flutter:
        signals.append("Flutter pubspec")
        return "adaptive", 0.92, signals
    if kmp:
        signals.append("Kotlin Multiplatform/Compose Multiplatform configuration")
        return "adaptive", 0.9, signals
    if ios_markers and android_markers:
        signals.append("concrete iOS and Android targets")
        return "adaptive", 0.88, signals
    if ios_markers:
        signals.append("iOS native target markers")
        return "ios", 0.84, signals
    if android_markers:
        signals.append("Android native target markers")
        return "android", 0.84, signals

    web_deps = {
        "@angular/core",
        "@sveltejs/kit",
        "@vitejs/plugin-react",
        "astro",
        "next",
        "nuxt",
        "react-dom",
        "svelte",
        "vite",
        "vue",
    }
    if deps & web_deps or has_any(target, ["index.html", "src/index.html", "app", "pages"]):
        signals.append("browser/web application markers")
        return "web", 0.78, signals
    signals.append("no native target detected; defaulting to web")
    return "web", 0.5, signals


def resolve_platform(
    target: Path,
    requested: str,
    product_path: Path | None,
) -> tuple[str, str, float, list[str], list[str]]:
    code_platform, code_confidence, code_signals = codebase_platform(target)
    product_platform, product_signals = parse_product_platform(product_path)
    contradictions: list[str] = []

    if requested != "auto":
        if product_platform and product_platform != requested:
            contradictions.append(f"explicit platform {requested} conflicts with PRODUCT.md {product_platform}")
        if code_confidence >= 0.8 and code_platform != requested:
            contradictions.append(f"explicit platform {requested} conflicts with codebase signal {code_platform}")
        return requested, "explicit", 1.0, product_signals + code_signals, contradictions
    if product_platform:
        if code_confidence >= 0.8 and code_platform != product_platform:
            contradictions.append(f"PRODUCT.md platform {product_platform} conflicts with codebase signal {code_platform}")
        return product_platform, "product_context", 0.95, product_signals + code_signals, contradictions
    if code_signals and code_confidence > 0.5:
        return code_platform, "codebase", code_confidence, code_signals, contradictions
    return "web", "default", 0.5, code_signals, contradictions


def line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def add_regex_findings(
    findings: list[Finding],
    *,
    path: Path,
    root: Path,
    text: str,
    platform: str,
    rules: Iterable[tuple[str, str, re.Pattern[str], str]],
) -> None:
    rel = str(path.relative_to(root))
    for rule_id, severity, pattern, message in rules:
        for match in pattern.finditer(text):
            findings.append(
                Finding(
                    rule_id=rule_id,
                    severity=severity,
                    platform=platform,
                    path=rel,
                    line=line_for_offset(text, match.start()),
                    message=message,
                )
            )


IOS_RULES = [
    (
        "ios.dynamic-type.fixed-size",
        "P1",
        re.compile(r"\.font\s*\(\s*\.system\s*\(\s*size\s*:", re.M),
        "Fixed SwiftUI point size can bypass Dynamic Type; use a text style or a scaling metric.",
    ),
    (
        "ios.navigation.edge-back-disabled",
        "P1",
        re.compile(r"\.navigationBarBackButtonHidden\s*\(\s*true\s*\)", re.M),
        "Hiding the system back control can disable the expected edge-swipe path.",
    ),
    (
        "ios.color.raw-rgb",
        "P2",
        re.compile(r"\b(?:Color|UIColor)\s*\(\s*(?:red\s*:|0x)", re.M),
        "Raw color construction should be reviewed against semantic system colors and appearance variants.",
    ),
    (
        "ios.safe-area.interactive-ignore",
        "P2",
        re.compile(r"\.ignoresSafeArea\s*\(\s*\.all", re.M),
        "Ignoring every safe area on an interactive surface risks controls under system regions.",
    ),
]

ANDROID_RULES = [
    (
        "android.type.dp-instead-of-sp",
        "P1",
        re.compile(r"fontSize\s*=\s*\d+(?:\.\d+)?\.dp\b", re.M),
        "Android text size must use sp/Material type roles rather than dp.",
    ),
    (
        "android.back.empty-handler",
        "P1",
        re.compile(r"BackHandler\s*\([^)]*\)\s*\{\s*\}", re.M | re.S),
        "An empty BackHandler traps system/predictive Back.",
    ),
    (
        "android.color.raw-argb",
        "P2",
        re.compile(r"\bColor\s*\(\s*0x[0-9A-Fa-f]{6,8}", re.M),
        "Raw ARGB should be reviewed against semantic Material color roles and theme variants.",
    ),
    (
        "android.touch-target.small-clickable",
        "P1",
        re.compile(r"Modifier\.(?:size|width|height)\s*\(\s*(?:[1-3]?\d|4[0-7])(?:\.\d+)?\.dp\s*\).*?\.clickable", re.M | re.S),
        "Clickable target appears smaller than the 48dp Android minimum.",
    ),
]

ADAPTIVE_RULES = [
    (
        "adaptive.device-model-branch",
        "P1",
        re.compile(r"UIDevice\.current\.(?:model|name)|\bBuild\.MODEL\b|DeviceInfo\.getModel\s*\(", re.M),
        "Drive adaptation from size/posture/capability rather than device model names.",
    ),
    (
        "adaptive.fixed-phone-canvas",
        "P2",
        re.compile(r"(?:width|height)\s*[:=]\s*(?:390|393|428|844|852|926)\b", re.M),
        "A fixed phone-canvas dimension in shared UI should be reviewed for tablet and multi-window adaptation.",
    ),
]


def scan_sources(target: Path, platform: str) -> list[Finding]:
    findings: list[Finding] = []
    for path in walk_files(target):
        suffix = path.suffix.lower()
        text = read_text(path)
        if not text:
            continue
        if platform in {"ios", "adaptive"} and suffix in {".swift", ".m", ".mm"}:
            add_regex_findings(findings, path=path, root=target, text=text, platform="ios", rules=IOS_RULES)
        if platform in {"android", "adaptive"} and suffix in {".kt", ".kts", ".java"}:
            add_regex_findings(findings, path=path, root=target, text=text, platform="android", rules=ANDROID_RULES)
        if platform == "adaptive" and suffix in {".dart", ".js", ".jsx", ".kt", ".kts", ".swift", ".ts", ".tsx"}:
            add_regex_findings(findings, path=path, root=target, text=text, platform="adaptive", rules=ADAPTIVE_RULES)
    unique: dict[tuple[str, str, int], Finding] = {}
    for finding in findings:
        unique[(finding.rule_id, finding.path, finding.line)] = finding
    return sorted(unique.values(), key=lambda item: (item.path, item.line, item.rule_id))


def runtime_contract(platform: str) -> dict[str, object]:
    mapping = {
        "web": ("browser", False, "tmwd_browser"),
        "ios": ("ios_simulator_and_device", True, "xcodebuild+simctl"),
        "android": ("android_emulator_and_device", True, "gradle+adb+emulator"),
        "adaptive": ("ios_and_android_runtimes", True, "xcodebuild+simctl+gradle+adb+emulator"),
    }
    kind, native, tool = mapping[platform]
    return {
        "runtime_validation_kind": kind,
        "native_validation_required": native,
        "preferred_runtime_tool": tool,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default=".")
    parser.add_argument("--platform", default="auto", choices=sorted(PLATFORMS))
    parser.add_argument("--product-context-path", default="")
    parser.add_argument("--mode", choices=["detect", "scan"], default="scan")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    target = resolve_target(args.target)
    if not target.is_dir():
        print(f"target is not a directory: {target}", file=sys.stderr)
        return 2

    product_path, product_path_source = discover_product_context(target, args.product_context_path)
    platform, source, confidence, signals, contradictions = resolve_platform(
        target,
        args.platform,
        product_path,
    )
    findings = scan_sources(target, platform) if args.mode == "scan" and platform != "web" else []
    severity_counts = {
        level: sum(1 for finding in findings if finding.severity == level)
        for level in ("P0", "P1", "P2", "P3")
    }
    payload = {
        "schema": SCHEMA,
        "ok": not any(finding.severity in {"P0", "P1"} for finding in findings),
        "target": str(target),
        "platform": platform,
        "platform_source": source,
        "platform_confidence": confidence,
        "product_context_path": str(product_path) if product_path and product_path.is_file() else "",
        "product_context_path_source": product_path_source,
        "product_context_status": "present" if product_path and product_path.is_file() else "missing",
        "signals": signals,
        "contradictions": contradictions,
        "scan_mode": args.mode,
        "findings": [asdict(finding) for finding in findings],
        "summary": {
            "total": len(findings),
            "severity_counts": severity_counts,
        },
        **runtime_contract(platform),
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"platform: {platform} ({source}, confidence={confidence:.2f})")
        print(f"product_context_path: {payload['product_context_path'] or 'unavailable'}")
        for signal in signals:
            print(f"signal: {signal}")
        for contradiction in contradictions:
            print(f"contradiction: {contradiction}")
        for finding in findings:
            print(
                f"{finding.severity} {finding.rule_id} "
                f"{finding.path}:{finding.line} {finding.message}"
            )

    if args.strict and (contradictions or not payload["ok"]):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
