from __future__ import annotations

from pathlib import Path

from .contract import read_text


def validate_output(task_dir: Path, host: str) -> list[str]:
    errors: list[str] = []
    output = task_dir / f"{host}-output.md"
    if not output.is_file():
        return [f"{output}: missing observed output"]
    text = read_text(output)
    if len(text.strip()) < 400:
        errors.append(f"{output}: observed output is too sparse")
    lowered = text.lower()
    required_concepts = {
        "evidence": ("evidence", "证据"),
        "unverified": ("unverified", "未验证", "未确认"),
        "design move": (
            "design move",
            "设计动作",
            "设计建议",
            "设计移动",
            "设计修正",
            "设计改进",
            "设计改动",
            "设计 move",
            "设计move",
        ),
    }
    for label, variants in required_concepts.items():
        if not any(variant in lowered for variant in variants):
            errors.append(f"{output}: output should cover the {label!r} concept")
    return errors
