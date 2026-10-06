from __future__ import annotations

import json
import sys

from .cli_parser import build_parser
from .contracts import ContractError


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except ContractError as error:
        print("review-craft contract validation failed:", file=sys.stderr)
        for item in error.errors:
            print(f"- {item}", file=sys.stderr)
        return 2
    except (OSError, ValueError, RuntimeError, KeyError, json.JSONDecodeError) as error:
        print(f"review-craft: {error}", file=sys.stderr)
        return 2
