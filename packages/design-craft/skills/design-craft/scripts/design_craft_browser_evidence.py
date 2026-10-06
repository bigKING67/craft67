#!/usr/bin/env python3
"""Emit and validate redacted browser evidence for product UI taste reviews."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


EVIDENCE_JS = r"""return (() => {
  const MAX_TEXT = 96;
  const redact = (value) => String(value || "")
    .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, "[email]")
    .replace(/\b(?:Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+/gi, "[auth]")
    .replace(/\b(?:sk|pk|ak|api|token|secret|key)[-_]?[A-Za-z0-9]{12,}\b/gi, "[secret]")
    .replace(/[A-Za-z0-9._-]+\.(?:json|env|pem|key|p12|txt)/g, "[file]")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, MAX_TEXT);
  const visible = (el) => {
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    return rect.width > 0 && rect.height > 0 && style.visibility !== "hidden" && style.display !== "none";
  };
  const pick = (el) => {
    const style = getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    return {
      tag: el.tagName.toLowerCase(),
      role: el.getAttribute("role") || "",
      text: redact(el.innerText || el.textContent || el.getAttribute("aria-label") || ""),
      fontSize: style.fontSize,
      fontWeight: style.fontWeight,
      lineHeight: style.lineHeight,
      color: style.color,
      backgroundColor: style.backgroundColor,
      borderColor: style.borderColor,
      borderRadius: style.borderRadius,
      boxShadow: style.boxShadow === "none" ? "none" : "present",
      outline: style.outlineStyle === "none" ? "none" : `${style.outlineWidth} ${style.outlineStyle} ${style.outlineColor}`,
      padding: style.padding,
      rect: {
        x: Math.round(rect.x),
        y: Math.round(rect.y),
        width: Math.round(rect.width),
        height: Math.round(rect.height)
      }
    };
  };
  const nodes = (selector, limit) => [...document.querySelectorAll(selector)].filter(visible).slice(0, limit).map(pick);
  const focusables = [...document.querySelectorAll("a,button,input,select,textarea,[tabindex]")].filter(visible);
  return {
    schema: "design-craft.browser-evidence.v1",
    source: {
      url: location.href,
      title: document.title,
      collectedAt: new Date().toISOString()
    },
    viewport: {
      innerWidth,
      innerHeight,
      devicePixelRatio,
      scrollX,
      scrollY,
      scrollWidth: document.documentElement.scrollWidth,
      scrollHeight: document.documentElement.scrollHeight,
      horizontalOverflow: document.documentElement.scrollWidth > innerWidth + 1
    },
    body: pick(document.body),
    headings: nodes("h1,h2,h3,[role='heading']", 8),
    controls: nodes("button,a,[role='button'],input,select,textarea", 12),
    surfaces: nodes("main,section,article,.card,[class*='card'],[class*='panel'],[class*='surface'],[class*='tile']", 12),
    stateSample: {
      activeElement: pick(document.activeElement || document.body),
      focusableCount: focusables.length
    },
    metrics: {
      headingCount: document.querySelectorAll("h1,h2,h3,[role='heading']").length,
      controlCount: focusables.length,
      surfaceCount: document.querySelectorAll("main,section,article,.card,[class*='card'],[class*='panel'],[class*='surface'],[class*='tile']").length
    },
    limits: {
      textMaxChars: MAX_TEXT,
      screenshotsIncluded: false,
      secretsRedacted: true
    }
  };
})();"""


SECRET_PATTERNS = [
    re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I),
    re.compile(r"\b(?:Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+", re.I),
    re.compile(r"\b(?:sk|pk|ak|api|token|secret|key)[-_]?[A-Za-z0-9]{12,}\b", re.I),
]
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
ALLOWED_EVIDENCE_SCHEMAS = {
    "design-craft.browser-evidence.v1",
}


def parse_level(value: str | None) -> int:
    if not value or not re.fullmatch(r"L[0-4]", value):
        return -1
    return int(value[1])


def walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(walk_strings(item))
        return result
    if isinstance(value, dict):
        result = []
        for item in value.values():
            result.extend(walk_strings(item))
        return result
    return []


def valid_dimension_pair(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(item, int) and item > 0 for item in value)
    )


def valid_score_range(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(item, int) for item in value)
        and value[0] <= value[1]
    )


def valid_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256_PATTERN.fullmatch(value))


def validate_evidence_json(path: Path) -> list[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - validation path
        return [f"{path}: invalid JSON: {exc}"]

    errors: list[str] = []
    if payload.get("schema") not in ALLOWED_EVIDENCE_SCHEMAS:
        errors.append(
            f"{path}: schema must be one of {sorted(ALLOWED_EVIDENCE_SCHEMAS)}"
        )
    for key in (
        "source",
        "viewport",
        "body",
        "headings",
        "controls",
        "surfaces",
        "stateSample",
        "metrics",
        "limits",
    ):
        if key not in payload:
            errors.append(f"{path}: missing {key}")
    viewport = payload.get("viewport", {})
    if not isinstance(viewport.get("innerWidth"), int) or not isinstance(viewport.get("innerHeight"), int):
        errors.append(f"{path}: viewport must include integer innerWidth and innerHeight")
    limits = payload.get("limits", {})
    if limits.get("secretsRedacted") is not True:
        errors.append(f"{path}: limits.secretsRedacted must be true")
    for text in walk_strings(payload):
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"{path}: possible unredacted secret or identifier: {text[:80]}")
                return errors
    return errors


def validate_score_json(path: Path) -> list[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path}: invalid JSON: {exc}"]

    errors: list[str] = []
    entries = payload.get("cases") if isinstance(payload.get("cases"), list) else [payload]
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"{path}: case at index {index} must be an object")
            continue
        case_id = entry.get("case_id") or payload.get("case_id") or path.parent.name
        level = entry.get("evidence_level") or payload.get("evidence_level")
        score = entry.get("expected_score")
        findings = " ".join(str(item).lower() for item in entry.get("required_findings", []))
        guards = " ".join(str(item).lower() for item in entry.get("false_positive_guards", []))
        evidence_text = f"{findings} {guards}"
        parsed_level = parse_level(level)

        if not isinstance(score, int):
            continue
        if "acceptable_range" in entry and not valid_score_range(entry.get("acceptable_range")):
            errors.append(f"{path}: {case_id} acceptable_range must be two ascending integers")
        if "screenshot_sha256" in entry and not valid_sha256(entry.get("screenshot_sha256")):
            errors.append(f"{path}: {case_id} screenshot_sha256 must be a lowercase 64-character SHA-256")
        dimensions = entry.get("screenshot_dimensions")
        if dimensions is not None and not valid_dimension_pair(dimensions):
            errors.append(f"{path}: {case_id} screenshot_dimensions must be two positive integers")
        if score > 84 and ("card soup" in evidence_text or "flat hierarchy" in evidence_text):
            errors.append(f"{path}: {case_id} scores above 84 despite flat hierarchy/card-soup finding")
        if score > 88 and parsed_level <= 1:
            errors.append(f"{path}: {case_id} scores above 88 without L2+ evidence")
        if score > 92 and parsed_level < 3:
            errors.append(f"{path}: {case_id} scores above 92 without L3+ responsive/state evidence")
        if score > 95 and parsed_level < 4:
            errors.append(f"{path}: {case_id} scores above 95 without L4 before/after evidence")
        if parsed_level < 3 and re.search(r"\b(mobile|responsive|hover|focus|loading|empty|error|keyboard)\b verified", evidence_text):
            errors.append(f"{path}: {case_id} claims state/responsive verification below L3")
        if parsed_level >= 3:
            viewports = entry.get("responsive_viewports")
            if not isinstance(viewports, list) or len(viewports) < 2:
                errors.append(f"{path}: {case_id} L3+ evidence must include at least two responsive_viewports")
            else:
                for viewport_index, viewport in enumerate(viewports):
                    if not isinstance(viewport, dict):
                        errors.append(f"{path}: {case_id} responsive_viewports[{viewport_index}] must be an object")
                        continue
                    css_size = viewport.get("css_size")
                    dimensions = viewport.get("dimensions")
                    if not isinstance(viewport.get("name"), str) or not viewport.get("name"):
                        errors.append(f"{path}: {case_id} responsive_viewports[{viewport_index}].name is required")
                    if not valid_dimension_pair(css_size):
                        errors.append(f"{path}: {case_id} responsive_viewports[{viewport_index}].css_size must be two positive integers")
                    if not valid_dimension_pair(dimensions):
                        errors.append(f"{path}: {case_id} responsive_viewports[{viewport_index}].dimensions must be two positive integers")
                    if "artifact_sha256" in viewport and not valid_sha256(viewport.get("artifact_sha256")):
                        errors.append(f"{path}: {case_id} responsive_viewports[{viewport_index}].artifact_sha256 must be a lowercase 64-character SHA-256")
                    if not isinstance(viewport.get("horizontal_overflow"), bool):
                        errors.append(f"{path}: {case_id} responsive_viewports[{viewport_index}].horizontal_overflow must be boolean")
            if not isinstance(entry.get("state_checks"), dict) or not entry.get("state_checks"):
                errors.append(f"{path}: {case_id} L3+ evidence must include state_checks")
        for artifact_index, artifact in enumerate(entry.get("selector_or_clip_artifacts", [])):
            if not isinstance(artifact, dict):
                errors.append(f"{path}: {case_id} selector_or_clip_artifacts[{artifact_index}] must be an object")
                continue
            if "artifact_sha256" in artifact and not valid_sha256(artifact.get("artifact_sha256")):
                errors.append(f"{path}: {case_id} selector_or_clip_artifacts[{artifact_index}].artifact_sha256 must be a lowercase 64-character SHA-256")
            if "dimensions" in artifact and not valid_dimension_pair(artifact.get("dimensions")):
                errors.append(f"{path}: {case_id} selector_or_clip_artifacts[{artifact_index}].dimensions must be two positive integers")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Product UI browser evidence helper.")
    parser.add_argument("--print-js", action="store_true", help="Print the TMWD browser_execute_js snippet.")
    parser.add_argument("--check", action="store_true", help="Run built-in helper checks.")
    parser.add_argument("--validate-evidence-json", action="append", default=[], help="Validate a captured DOM/style evidence JSON file.")
    parser.add_argument("--validate-score-json", action="append", default=[], help="Validate product UI taste score anti-inflation rules.")
    args = parser.parse_args()

    if args.print_js:
        print(EVIDENCE_JS)

    errors: list[str] = []
    if args.check:
        if "design-craft.browser-evidence.v1" not in EVIDENCE_JS:
            errors.append("evidence JS must include schema marker")
        if "[email]" not in EVIDENCE_JS or "[secret]" not in EVIDENCE_JS:
            errors.append("evidence JS must include redaction markers")
    for item in args.validate_evidence_json:
        errors.extend(validate_evidence_json(Path(item)))
    for item in args.validate_score_json:
        errors.extend(validate_score_json(Path(item)))

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
