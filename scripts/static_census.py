#!/usr/bin/env python3
"""Privacy-minimizing, offline structural census of untrusted saved website captures.

Emits only allowlisted labels and numeric/boolean observations. No source text,
URLs, identifiers, filenames or raw capture contents are ever present in output.
"""
from __future__ import annotations

import argparse
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import stat
import sys
import zipfile

from viewsource import (
    ROOT, WORKDIR, MAX_SCAN_BYTES, MAX_MEMBER_COUNT, MAX_TOTAL_UNCOMPRESSED,
    safe_entry,
)

COUNTED_TAGS = (
    "html", "head", "body", "header", "nav", "main", "aside", "section",
    "article", "div", "span", "a", "button", "form", "input", "textarea",
    "select", "script", "style", "link", "meta", "img", "svg", "iframe",
    "picture", "source", "video", "audio", "dialog", "template"
)
COUNTED_ARIA = (
    "aria-label", "aria-labelledby", "aria-expanded", "aria-controls",
    "aria-hidden", "aria-current", "role", "data-state"
)
COUNTERS = (
    "external_script", "inline_executable_script", "inline_json_script",
    "external_stylesheet", "inline_style", "external_image", "inline_svg",
    "file_input", "multiple_file_input", "capture_file_input",
    "react_router_stream_script", "react_boundary_helper_script",
    "session_storage_script", "local_storage_script", "theme_bootstrap_script",
    "media_rules", "reduced_motion_rules", "hover_rules", "width_rules",
    "custom_property_declarations", "script_inline_code_characters",
    "script_inline_json_characters", "style_inline_characters",
)
SIGNALS = (
    "account_linked_attribute_present", "serialized_application_state_present",
    "desktop_context_attribute_present",
)
MAX_SCAN_PAGES = 500

class StaticCensus(HTMLParser):
    """Record structural counts only; never retain attribute values or page data."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = Counter()
        self.attributes = Counter()
        self.counts = Counter()
        self.signals = {name: False for name in SIGNALS}
        self._script = None
        self._style = None

    def handle_starttag(self, tag, attrs):
        if tag in COUNTED_TAGS:
            self.tags[tag] += 1
        a = dict(attrs)
        for name in COUNTED_ARIA:
            if name in a:
                self.attributes[name] += 1
        if any(k.startswith("data-theme-user-") or
               k.startswith("data-theme-account-") or
               k in {"data-user-id", "data-account-id"} for k in a):
            self.signals["account_linked_attribute_present"] = True
        if any(k.startswith("data-codex-window") or k == "data-codex-os" for k in a):
            self.signals["desktop_context_attribute_present"] = True
        if tag == "script":
            self._script = {"data": False, "pieces": []}
            if a.get("src") is not None:
                self.counts["external_script"] += 1
                self._script = None
            elif (a.get("type") or "").lower() in {"application/json", "application/ld+json"}:
                self.counts["inline_json_script"] += 1
                self.signals["serialized_application_state_present"] = True
                self._script["data"] = True
            else:
                self.counts["inline_executable_script"] += 1
        elif tag == "style":
            self.counts["inline_style"] += 1
            self._style = []
        elif tag == "link" and "stylesheet" in (a.get("rel") or "").lower().split():
            self.counts["external_stylesheet"] += 1
        elif tag == "img":
            self.counts["external_image"] += int(bool(a.get("src")))
        elif tag == "svg":
            self.counts["inline_svg"] += 1
        elif tag == "input" and (a.get("type") or "").lower() == "file":
            self.counts["file_input"] += 1
            self.counts["multiple_file_input"] += int("multiple" in a)
            self.counts["capture_file_input"] += int("capture" in a)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag in {"script", "style"}:
            self.handle_endtag(tag)

    def handle_data(self, data):
        if self._script is not None:
            if self._script["data"]:
                # Count only: never keep serialized user or application data in memory.
                self.counts["script_inline_json_characters"] += len(data)
            else:
                self._script["pieces"].append(data)
                self.counts["script_inline_code_characters"] += len(data)
        if self._style is not None:
            self._style.append(data)
            self.counts["style_inline_characters"] += len(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._script is not None:
            if not self._script["data"]:
                body = "".join(self._script["pieces"])
                for counter, signature in (
                    ("react_router_stream_script", "__reactRouterContext.streamController"),
                    ("react_boundary_helper_script", "$RC("),
                    ("session_storage_script", "sessionStorage"),
                    ("local_storage_script", "localStorage"),
                    ("theme_bootstrap_script", "prefers-color-scheme"),
                ):
                    self.counts[counter] += int(signature in body)
            self._script = None
        elif tag == "style" and self._style is not None:
            css = "".join(self._style)
            self.counts["media_rules"] += len(re.findall(r"@media\s*\(", css, re.I))
            self.counts["reduced_motion_rules"] += len(re.findall(r"@media\s*\(\s*prefers-reduced-motion\b", css, re.I))
            self.counts["hover_rules"] += len(re.findall(r"@media\s*\(\s*hover\b", css, re.I))
            self.counts["width_rules"] += len(re.findall(r"@media\s*\(\s*(?:min-width|max-width|width)\b", css, re.I))
            self.counts["custom_property_declarations"] += len(re.findall(r"--[a-z][\w-]*\s*:", css, re.I))
            self._style = None

    def report(self):
        return {
            "tag_counts": {name: self.tags[name] for name in COUNTED_TAGS},
            "attribute_counts": {name: self.attributes[name] for name in COUNTED_ARIA},
            "resource_and_script_counts": {name: self.counts[name] for name in COUNTERS},
            "presence_flags": self.signals.copy(),
        }


def scan_html(content: bytes):
    if len(content) > MAX_SCAN_BYTES:
        raise ValueError("HTML file exceeds static census scan limit")
    census = StaticCensus()
    census.feed(content.decode("utf-8", errors="replace"))
    census.close()
    return census.report()


def scan_capture(path: Path):
    absolute = path.resolve(strict=True)
    if not absolute.is_file():
        raise ValueError("Input must be a regular file")
    if absolute.is_relative_to(ROOT.resolve()):
        raise ValueError("Source capture must remain outside the public repository")

    suffix = absolute.suffix.lower()
    files = []
    omitted = 0
    if suffix in {".html", ".htm", ".xhtml"}:
        files.append(absolute.read_bytes())
        kind = "saved_page"
    elif suffix == ".zip":
        kind = "saved_archive"
        with zipfile.ZipFile(absolute) as archive:
            entries = [e for e in archive.infolist() if not e.is_dir()]
            if len(entries) > MAX_MEMBER_COUNT:
                raise ValueError("Archive member-count limit exceeded")
            total = 0
            for entry in entries:
                if not safe_entry(entry.filename) or stat.S_ISLNK(entry.external_attr >> 16):
                    raise ValueError("Unsafe archive entry")
                total += entry.file_size
                if total > MAX_TOTAL_UNCOMPRESSED:
                    raise ValueError("Archive uncompressed-size limit exceeded")
                if entry.file_size and entry.file_size / max(entry.compress_size, 1) > 1000:
                    raise ValueError("Suspicious archive compression ratio")
            for entry in entries:
                if not entry.filename.lower().endswith((".html", ".htm", ".xhtml")):
                    continue
                if entry.file_size > MAX_SCAN_BYTES or len(files) >= MAX_SCAN_PAGES:
                    omitted += 1
                    continue
                with archive.open(entry) as stream:
                    files.append(stream.read(MAX_SCAN_BYTES + 1))
    else:
        raise ValueError("Provide saved HTML or a ZIP archive")
    all_counts = Counter()
    tag_counts = Counter()
    attr_counts = Counter()
    flags = {name: False for name in SIGNALS}
    for content in files:
        result = scan_html(content)
        tag_counts.update(result["tag_counts"])
        attr_counts.update(result["attribute_counts"])
        all_counts.update(result["resource_and_script_counts"])
        for name, value in result["presence_flags"].items():
            flags[name] = flags[name] or value
    return {
        "format_version": 1, "capture_scope": kind,
        "pages_inspected": len(files), "pages_omitted": omitted,
        "tag_counts": {name: tag_counts[name] for name in COUNTED_TAGS},
        "attribute_counts": {name: attr_counts[name] for name in COUNTED_ARIA},
        "resource_and_script_counts": {name: all_counts[name] for name in COUNTERS},
        "presence_flags": flags,
        "limitations": [
            "Aggregate static markup only; no scripts executed or network requests made.",
            "No page text, source URLs, paths, private identifiers, or serialized application data in output.",
            "This summary does not establish live behavior, full-site coverage, or publication rights."
        ]
    }


def main():
    parser = argparse.ArgumentParser(description="Produce a private aggregate structural census")
    parser.add_argument("--input", required=True, type=Path, help="HTML or ZIP capture outside this repository")
    parser.add_argument("--slug", required=True, help="Existing public specimen slug")
    parser.add_argument("--version", type=int, required=True, help="Existing internal capture version number")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z][a-z0-9-]{1,47}", args.slug) or args.slug.endswith("-") or args.version < 1:
        parser.error("Provide a valid specimen slug and positive version")
    try:
        target = ROOT / "specimens" / args.slug / f"v{args.version:04d}" / "record.json"
        if not target.is_file():
            raise ValueError("Queue/process this specimen version before running its census")
        result = scan_capture(args.input)
        output = WORKDIR / args.slug / f"v{args.version:04d}" / "static-census.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"Private census recorded: {result['pages_inspected']} HTML page(s) scanned, "
              f"{result['pages_omitted']} omitted; no source data published")
        return 0
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"Error: {type(exc).__name__}; no census created", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
