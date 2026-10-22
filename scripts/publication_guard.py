#!/usr/bin/env python3
"""Check tracked paths and high-confidence publication leaks; not a rights clearance."""
from __future__ import annotations

import re
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PROHIBITED_SUFFIXES = {".zip", ".mhtml", ".warc", ".har", ".sqlite", ".db"}
CAPTURE_SUFFIXES = {".html", ".htm", ".xhtml", ".js", ".mjs", ".css", ".svg", ".png", ".jpg", ".jpeg", ".webp", ".woff", ".woff2", ".ttf", ".otf", ".mp4", ".webm"}
PRIVATE_SEGMENTS = {".work", "capture", "captures", "download", "downloads", "raw", "secrets", "browser-profile", "evidence"}
KEY_PATTERNS = [
    re.compile(r"-----BEGIN" + r" (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.I),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
    re.compile(r"(?i)\bauthorization\s*:\s*bearer\s+[a-z0-9._~+/=-]{16,}"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@(?:gmail|yahoo|hotmail|outlook)\.[A-Za-z]{2,}\b", re.I)
]

# Catch common public-account identity formats and credential-bearing URLs.
# This checks text shapes, not user-specific values. Real personal identifiers
# must never be used as test fixtures or scanner examples.
SENSITIVE_PATTERNS = KEY_PATTERNS + [
    re.compile(r"\buser-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\borg-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{12,}\b"),
    re.compile(r'https?://[^\s"<>]+[?&](?:access_token|session|api_key|auth|token|code)=[^\s&#"<>]+', re.I),
]


def contains_sensitive_shape(content: str) -> bool:
    """Check patterns without echoing matched material into logs."""
    return any(signature.search(content) is not None for signature in SENSITIVE_PATTERNS)


def scan() -> list[str]:
    listed = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    failures = []
    for raw in listed.split(b"\0"):
        if not raw:
            continue
        rel = Path(raw.decode("utf-8", errors="replace"))
        normalized = rel.as_posix()
        path = ROOT / rel
        if any(segment.lower() in PRIVATE_SEGMENTS for segment in rel.parts):
            failures.append(f"Forbidden private workspace path: {normalized}")
            continue
        if path.suffix.lower() in PROHIBITED_SUFFIXES:
            failures.append(f"Forbidden capture/archive type: {normalized}")
            continue
        if rel.parts[0] == "specimens" and path.suffix.lower() in CAPTURE_SUFFIXES:
            failures.append(f"Raw specimen resource type: {normalized}")
            continue
        if not path.is_file():
            continue
        if path.stat().st_size > 1024 * 1024:
            failures.append(f"Review unusually large tracked file: {normalized}")
            continue
        if path.suffix.lower() not in {".py", ".md", ".json", ".yaml", ".yml", ".toml", ".txt", ".gitignore", ".html", ".js", ".css"} and path.name not in {"LICENSE", ".gitignore"}:
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        if contains_sensitive_shape(content):
            failures.append(f"Potential secret or private identifier: {normalized}")
    return failures


if __name__ == "__main__":
    try:
        problems = scan()
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"Publication guard could not complete: {exc}", file=sys.stderr)
        sys.exit(1)
    for issue in problems:
        print(issue, file=sys.stderr)
    if problems:
        sys.exit(1)
    print("Tracked-file publication guard passed (manual rights and content review still required)")
