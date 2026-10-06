"""Use the canonical validators/compiler with source-checkout image profiles."""
from __future__ import annotations

import json
import sys
from pathlib import Path

if sys.version_info < (3, 11):
    print(json.dumps({"valid": False, "error": "python_version"}))
    sys.exit(2)

import tomllib

MODULE = Path(__file__).resolve().parent
SKILL = MODULE.parents[1] / "skills" / "creative-craft"
sys.path.insert(0, str(SKILL / "scripts"))
from creative_craft_contracts import ValidationContext, validate_data
from creative_craft_evaluation import compile_image_markdown


class ImageContext(ValidationContext):
    @property
    def providers_dir(self) -> Path:
        return MODULE / "providers"


def main() -> None:
    command = sys.argv[1]
    if command == "config":
        root = Path(sys.argv[2])
        config = tomllib.loads((root / "config.toml").read_text())
        provider = config["model_provider"]
        selected = config["model_providers"][provider]
        auth = json.loads((root / "auth.json").read_text())
        # This stdout is captured in memory by the Node caller, never forwarded.
        print(json.dumps({"base_url": selected["base_url"], "api_key": auth["OPENAI_API_KEY"],
                          "provider": provider, "wire_api": selected.get("wire_api")}))
        return
    data = json.load(sys.stdin)
    kind, result = validate_data(data, context=ImageContext())
    if not result.ok:
        print(json.dumps({"valid": False, "errors": result.errors}))
        return
    output = {"valid": True, "kind": kind, "warnings": result.warnings}
    if command == "compile":
        if kind != "image":
            raise ValueError("Expected image job")
        pack = compile_image_markdown(data)
        # The prompt is the single fenced block; a fence inside any field would silently truncate it.
        if pack.count("```") != 2:
            print(json.dumps({"valid": False, "errors": ["job text fields must not contain ``` code fences"]}))
            return
        output.update(pack=pack, prompt=pack.split("```text\n", 1)[1].split("\n```", 1)[0])
    elif command != "validate":
        raise ValueError("Unknown contract command")
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, IndexError, TypeError, RuntimeError):
        # Config/auth parse errors must not echo file contents or credentials.
        print(json.dumps({"valid": False, "error": "Config or contract input rejected"}))
        sys.exit(1)
