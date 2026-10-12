"""Read-only, stdlib-only verification of a saved DOCX package.

This verifier NEVER starts Word, edits the document, or infers success from an
agent report. Input must be an explicit path to a local DOCX artifact.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import zipfile
from xml.etree import ElementTree as ET

WORD_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
MAX_DOCX_BYTES = 40 * 1024 * 1024
MAX_XML_BYTES = 12 * 1024 * 1024


def verify_docx(path: Path, expected_text: str) -> dict:
    report = {"path": str(path), "verified": False, "status": "not_checked",
              "expected_text_matched": False, "paragraph_count": 0}
    if not expected_text.strip():
        report["status"] = "empty_expected_text"
        return report
    if not path.is_file() or path.is_symlink():
        report["status"] = "file_missing"
        return report
    if path.suffix.lower() != ".docx":
        report["status"] = "not_docx_extension"
        return report
    if path.stat().st_size > MAX_DOCX_BYTES:
        report["status"] = "file_too_large"
        return report
    try:
        with zipfile.ZipFile(path) as package:
            names = set(package.namelist())
            if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                report["status"] = "invalid_docx_package"
                return report
            info = package.getinfo("word/document.xml")
            if info.file_size > MAX_XML_BYTES:
                report["status"] = "document_xml_too_large"
                return report
            document = ET.fromstring(package.read(info))
    except (OSError, ValueError, zipfile.BadZipFile, ET.ParseError, RuntimeError):
        report["status"] = "unreadable_docx"
        return report
    paragraphs = []
    for p in document.iter(WORD_NS + "p"):
        text = "".join(node.text or "" for node in p.iter(WORD_NS + "t"))
        paragraphs.append(text)
    report["paragraph_count"] = len(paragraphs)
    actual_text = "\n".join(paragraphs)
    report["expected_text_matched"] = expected_text in actual_text
    report["verified"] = report["expected_text_matched"]
    report["status"] = "verified" if report["verified"] else "content_mismatch"
    return report


def expected_text_from_request(request: str) -> str | None:
    """Only accept an explicit, bounded exact-content contract; never guess."""
    pattern = r"\[DOCX_EXPECTED_TEXT\]([\s\S]*?)\[/DOCX_EXPECTED_TEXT\]"
    matches = list(re.finditer(pattern, request, re.IGNORECASE))
    # Ambiguous, repeated or unpaired markers must not silently select a subset.
    opens = len(re.findall(r"\[DOCX_EXPECTED_TEXT\]", request, re.IGNORECASE))
    closes = len(re.findall(r"\[/DOCX_EXPECTED_TEXT\]", request, re.IGNORECASE))
    if len(matches) != 1 or opens != 1 or closes != 1:
        return None
    value = matches[0].group(1).strip()
    return value if 0 < len(value) <= 4000 else None


def verify_docx_package(path: Path) -> dict:
    """Read-only structural check; success here never proves requested content."""
    result = {"package_valid": False, "package_status": "not_checked"}
    if path.is_symlink() or not path.is_file():
        result["package_status"] = "file_missing"
        return result
    if path.suffix.lower() != ".docx":
        result["package_status"] = "not_docx_extension"
        return result
    if path.stat().st_size > MAX_DOCX_BYTES:
        result["package_status"] = "file_too_large"
        return result
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                result["package_status"] = "invalid_docx_package"
                return result
            info = archive.getinfo("word/document.xml")
            if info.file_size > MAX_XML_BYTES:
                result["package_status"] = "document_xml_too_large"
                return result
            document = ET.fromstring(archive.read(info))
            if document.tag != WORD_NS + "document":
                result["package_status"] = "invalid_document_root"
                return result
    except (OSError, ValueError, zipfile.BadZipFile, ET.ParseError, RuntimeError):
        result["package_status"] = "unreadable_docx"
        return result
    result.update(package_valid=True, package_status="valid_docx_package")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--expected", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify_docx(args.file, args.expected)
    report = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print("Saved:", args.output)
    else:
        print(report)
    return 0 if result["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
