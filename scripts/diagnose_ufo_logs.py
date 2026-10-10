"""Offline UFO diagnostic: identify reliability failure types without dumping secrets.

Usage: python scripts/diagnose_ufo_logs.py vendor/UFO/logs/lol-existing-window-test
The tool never prints raw request/response content or credentials.
"""
import argparse
import pathlib
import re
import sys

CATEGORIES = {
    "uia_empty": re.compile(r"UIA control collection failed|NoneType.{0,25}len\(", re.I),
    "json_parse": re.compile(r"Expecting ',' delimiter|LLM response parsing failed|JSONDecodeError", re.I),
    "app_llm_failed": re.compile(r"AppLLMInteractionStrategy.*(?:failed|ERROR)|ProcessingPhase\.LLM_INTERACTION", re.I),
    "blocked_launch": re.compile(r"Blocked CLI command|Command blocked by security policy", re.I),
    "provider_error": re.compile(r"ClientError|RESOURCE_EXHAUSTED|429|404", re.I),
}
TEXT_EXTENSIONS = {".log", ".txt", ".md", ".json", ".jsonl"}
MAX_FILE_BYTES = 25_000_000


def scan(root: pathlib.Path) -> dict[str, int]:
    counts = dict.fromkeys(CATEGORIES, 0)
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        if path.is_symlink() or path.stat().st_size > MAX_FILE_BYTES:
            continue
        try:
            with path.open("r", encoding="utf-8", errors="replace") as file:
                for line in file:
                    for key, pattern in CATEGORIES.items():
                        if pattern.search(line):
                            counts[key] += 1
        except OSError:
            continue
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_folder", type=pathlib.Path)
    args = parser.parse_args()
    if not args.log_folder.is_dir():
        print("ERROR: log folder does not exist", file=sys.stderr)
        return 2
    counts = scan(args.log_folder)
    print("UFO ERROR SUMMARY (counts are log mentions, not independent failures)")
    for key, count in counts.items():
        print(f"{key}: {count}")
    print("Raw prompts, model responses, and API keys were not printed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
