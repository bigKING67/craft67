from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .common import ReverseCraftError, load_json, sha256_file

MAGIC = (
    (b"\x7fELF", "ELF binary", " .elf binary "),
    (b"MZ", "PE executable", " pe executable "),
    (b"PK\x03\x04", "ZIP/APK/JAR container", " zip apk jar "),
    (b"\xca\xfe\xba\xbe", "Java class or Mach-O universal", " java mach-o "),
    (b"\xcf\xfa\xed\xfe", "Mach-O 64-bit", " mach-o macos "),
    (b"\xfe\xed\xfa\xcf", "Mach-O 64-bit (big endian)", " mach-o macos "),
    (b"\x00asm", "WebAssembly module", " wasm reverse "),
    (b"dex\n", "Android DEX", " android apk dex "),
    (b"SQLite format 3\x00", "SQLite database", " sqlite database "),
    (b"\xd4\xc3\xb2\xa1", "PCAP capture", " pcap protocol wireshark "),
    (b"\x0a\x0d\x0d\x0a", "PCAP-NG capture", " pcap protocol wireshark "),
)


def reference_root() -> Path:
    return Path(__file__).resolve().parents[2] / "references"


def artifact_hint(raw_path: str) -> dict[str, Any]:
    path = Path(raw_path).expanduser().resolve()
    if not path.exists():
        raise ReverseCraftError(f"artifact not found: {path}")
    result: dict[str, Any] = {"path": str(path), "name": path.name, "kind": "directory" if path.is_dir() else "file"}
    if path.is_dir():
        result["routing_text"] = f" directory {path.name} "
        return result
    stat = path.stat()
    with path.open("rb") as handle:
        head = handle.read(64)
    magic_name = "unknown"
    magic_text = ""
    for prefix, label, routing_text in MAGIC:
        if head.startswith(prefix):
            magic_name = label
            magic_text = routing_text
            break
    result.update({
        "size": stat.st_size,
        "suffix": path.suffix.lower(),
        "magic": magic_name,
        "head_hex": head.hex(),
        "sha256": sha256_file(path) if stat.st_size <= 64 * 1024 * 1024 else None,
        "routing_text": f" {path.name} {path.suffix} {magic_name} {magic_text} ",
    })
    return result


def _matches(pattern: str | None, text: str) -> bool:
    if not pattern:
        return False
    try:
        return re.search(pattern, text, re.IGNORECASE) is not None
    except re.error as exc:
        raise ReverseCraftError(f"invalid route regex {pattern!r}: {exc}") from exc


def route(hint: str, artifact: str | None = None) -> dict[str, Any]:
    root = reference_root()
    config = load_json(root / "upstream" / "reverse-skill-routing.json")
    modules = load_json(root / "modules.json")["routes"]
    artifact_data = artifact_hint(artifact) if artifact else None
    combined = f" {hint.strip()} " + (artifact_data.get("routing_text", "") if artifact_data else "")
    routes = config["routes"]
    priority = config["priority"]
    fallback = config["meta"]["fallbackId"]
    candidates: list[dict[str, Any]] = []
    for route_id in priority:
        route_def = routes[route_id]
        matched: list[dict[str, Any]] = []
        for index, rule in enumerate(route_def.get("keywords", [])):
            if not _matches(rule.get("must"), combined):
                continue
            if any(not _matches(pattern, combined) for pattern in rule.get("mustAll", [])):
                continue
            if _matches(rule.get("exclude"), combined):
                continue
            matched.append({
                "rule_index": index,
                "note": rule.get("note"),
                "fallback_only": rule.get("fallbackOnly") is True,
            })
        if matched:
            candidates.append({
                "id": route_id,
                "label": route_def["label"],
                "score": len(matched),
                "priority": priority.index(route_id),
                "matched_rules": matched,
            })
    if any(item["id"] != fallback for item in candidates):
        adjusted: list[dict[str, Any]] = []
        for item in candidates:
            if item["id"] == fallback:
                item["matched_rules"] = [
                    rule for rule in item["matched_rules"] if not rule["fallback_only"]
                ]
                item["score"] = len(item["matched_rules"])
                if not item["matched_rules"]:
                    continue
            adjusted.append(item)
        candidates = adjusted
    for item in candidates:
        for rule in item["matched_rules"]:
            rule.pop("fallback_only", None)
    if candidates:
        candidates.sort(key=lambda item: (-item["score"], item["priority"]))
        candidates = [{**item, **modules[item["id"]]} for item in candidates]
        primary = candidates[0]
        winning_score = primary["score"]
        tied = [item["id"] for item in candidates if item["score"] == winning_score]
    else:
        primary = {
            "id": fallback,
            "label": routes[fallback]["label"],
            "score": 0,
            "priority": priority.index(fallback),
            "matched_rules": [],
        }
        primary = {**primary, **modules[fallback]}
        candidates = [primary]
        tied = [fallback]
    return {
        "schema": "reverse-craft.route.v1",
        "hint": hint,
        "artifact": artifact_data,
        "primary": primary,
        "secondary": [item for item in candidates[1:5]],
        "ambiguous": len(tied) > 1,
        "tied": tied,
        "candidate_count": len(candidates),
        "routing_source": {
            "schema_version": config["schemaVersion"],
            "routes": len(routes),
            "sha256": sha256_file(root / "upstream" / "reverse-skill-routing.json"),
        },
    }
