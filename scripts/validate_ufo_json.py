"""Validate a UFO/Gemini JSON response offline without ever printing its contents.

Usage: python scripts/validate_ufo_json.py path/to/response.json
Validation is deliberately read-only: never auto-repair tool commands.
"""
import argparse
import json
import pathlib
import sys


def validate(raw: str) -> tuple[bool, str]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        # Don't output exc.doc or any model-produced content.
        return False, f"invalid-json: line={exc.lineno} column={exc.colno} offset={exc.pos}"
    if not isinstance(data, dict):
        return False, "invalid-shape: expected JSON object"
    return True, "valid-json-object (schema compatibility not verified)"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("response_file", type=pathlib.Path)
    args = parser.parse_args()
    path = args.response_file
    if not path.is_file() or path.stat().st_size > 2_000_000:
        print("ERROR: missing or oversized response file", file=sys.stderr)
        return 2
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        print("ERROR: unable to read UTF-8 response file", file=sys.stderr)
        return 2
    ok, verdict = validate(raw)
    print(verdict)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
