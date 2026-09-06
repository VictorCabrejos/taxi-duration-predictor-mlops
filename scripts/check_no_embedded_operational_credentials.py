"""Fail when tracked source embeds operational-looking database credentials."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SCANNED_SUFFIXES = {
    ".bat",
    ".cfg",
    ".env",
    ".example",
    ".ini",
    ".ipynb",
    ".json",
    ".ps1",
    ".py",
    ".sh",
    ".toml",
    ".yaml",
    ".yml",
}

PASSWORD_ASSIGNMENT = re.compile(
    r"(?i)(?:[\"']?\b(?:db_|database_|postgres_)?(?:password|passwd|pwd)\b[\"']?)"
    r"\s*(?::|=)\s*[\"']([^\"'\r\n]+)[\"']"
)
DATABASE_URL = re.compile(
    r"(?i)postgres(?:ql)?://[^:\s/\"']+:([^@\s/\"']+)@[^\s/\"']+"
)
PASSWORD_DOCUMENTATION = re.compile(
    r"(?i)\bpassword\b[^:\r\n]{0,12}:\s*`([^`\r\n]+)`"
)
RDS_HOST = re.compile(r"(?i)\b[a-z0-9.-]+\.rds\.amazonaws\.com\b")

PLACEHOLDER_MARKERS = (
    "${",
    "{",
    "}",
    "<",
    ">",
    "[",
    "]",
    "changeme",
    "change_me",
    "dummy",
    "example",
    "invalid",
    "password_from_env",
    "placeholder",
    "redacted",
    "your_",
    "xxxxx",
)


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule: str


def _is_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    return not normalized or any(marker in normalized for marker in PLACEHOLDER_MARKERS)


def scan_text(text: str, path: str) -> list[Finding]:
    findings = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for rule, pattern in (
            ("literal-password-assignment", PASSWORD_ASSIGNMENT),
            ("embedded-database-url-password", DATABASE_URL),
            ("documented-literal-password", PASSWORD_DOCUMENTATION),
        ):
            for match in pattern.finditer(line):
                if not _is_placeholder(match.group(1)):
                    findings.append(Finding(path, line_number, rule))
        for match in RDS_HOST.finditer(line):
            if not _is_placeholder(match.group(0)):
                findings.append(Finding(path, line_number, "operational-rds-host"))
    return findings


def _notebook_source(path: Path) -> Iterable[tuple[str, int]]:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    for cell_number, cell in enumerate(notebook.get("cells", []), start=1):
        yield "".join(cell.get("source", [])), cell_number


def _tracked_paths(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [root / item.decode() for item in result.stdout.split(b"\0") if item]


def scan_repository(root: Path) -> list[Finding]:
    findings = []
    for path in _tracked_paths(root):
        if path.suffix.lower() not in SCANNED_SUFFIXES or not path.is_file():
            continue
        relative_path = path.relative_to(root).as_posix()
        try:
            if path.suffix.lower() == ".ipynb":
                for source, cell_number in _notebook_source(path):
                    for finding in scan_text(source, relative_path):
                        findings.append(
                            Finding(relative_path, cell_number, f"cell:{finding.rule}")
                        )
            else:
                findings.extend(
                    scan_text(path.read_text(encoding="utf-8"), relative_path)
                )
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            findings.append(Finding(relative_path, 0, f"unscannable:{type(exc).__name__}"))
    return findings


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    findings = scan_repository(root)
    if findings:
        for finding in findings:
            print(f"{finding.path}:{finding.line}:{finding.rule}")
        print(f"FAIL: {len(findings)} operational credential pattern(s) found")
        return 1
    print("PASS: no embedded operational database credential patterns found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
