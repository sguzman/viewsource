#!/usr/bin/env python3
"""Offline, capture-isolating website specimen intake and research task generation."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import ipaddress
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys
from urllib.parse import urlsplit
import zipfile

ROOT = Path(__file__).resolve().parents[1]
WORKDIR = ROOT / ".work"
SLUG = re.compile(r"^[a-z][a-z0-9-]{1,47}$")
MAX_ARCHIVE_BYTES = 1024 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED = 512 * 1024 * 1024
MAX_MEMBER_COUNT = 30000
MAX_SCAN_BYTES = 8 * 1024 * 1024
# Candidate feature markers create research work, never verified findings.
# Only allowlisted feature labels enter public task metadata.
FEATURE_SCAN_MAX = 8 * 1024 * 1024

CATEGORIES = {
    ".html": "html", ".htm": "html", ".xhtml": "html",
    ".js": "script", ".mjs": "script", ".cjs": "script",
    ".css": "stylesheet", ".map": "source-map", ".json": "data",
    ".svg": "image", ".png": "image", ".jpg": "image", ".jpeg": "image",
    ".gif": "image", ".webp": "image", ".avif": "image", ".ico": "image",
    ".woff": "font", ".woff2": "font", ".ttf": "font", ".otf": "font",
    ".mp3": "audio", ".wav": "audio", ".ogg": "audio",
    ".mp4": "video", ".webm": "video",
    ".xml": "data", ".txt": "text"
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def slug_ok(slug: str) -> bool:
    return bool(SLUG.fullmatch(slug)) and not slug.endswith("-")


def public_origin(value: str) -> str:
    """Only public DNS origins; exclude credentials, paths, queries and local hosts."""
    parts = urlsplit(value)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError("Origin must be an http(s) public DNS origin")
    if parts.username or parts.password or parts.query or parts.fragment or parts.path not in {"", "/"}:
        raise ValueError("Origin must not include credentials, a path, query or fragment")
    host = parts.hostname.lower()
    if "." not in host or host.endswith((".local", ".internal", ".test")):
        raise ValueError("Origin requires a public DNS hostname")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError("IP origins are not recorded in public metadata")
    if not re.fullmatch(r"[a-z0-9.-]+", host) or ".." in host:
        raise ValueError("Origin hostname is invalid")
    try:
        port = parts.port
    except ValueError as exc:
        raise ValueError("Invalid origin port") from exc
    if port not in (None, 80, 443):
        raise ValueError("Nonstandard ports are not recorded in public metadata")
    return parts.scheme + "://" + host


class PageParser(HTMLParser):
    def __init__(self, feature_config: dict | None = None) -> None:
        super().__init__(convert_charrefs=True)
        self._feature_config = feature_config
        self.inline_feature_signals: dict[str, set[str]] = {}
        self.tags = Counter()
        self.scripts = []
        self.styles = []
        self.assets = []
        self.forms = []
        self.links = []
        self.metadata = []
        self.inline_handlers = Counter()
        self._script_depth = 0
        self._inline_script_chars = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags[tag] += 1
        a = dict(attrs)
        for key in a:
            if key.startswith("on") and len(key) > 2:
                self.inline_handlers[key] += 1
        if tag == "script":
            self.scripts.append({"src": a.get("src"), "type": a.get("type"),
                                 "async": "async" in a, "defer": "defer" in a})
            self._script_depth += 1
        elif tag == "link":
            rel = (a.get("rel") or "").lower()
            item = {"rel": rel, "href": a.get("href"), "as": a.get("as")}
            if "stylesheet" in rel:
                self.styles.append(item)
            else:
                self.links.append(item)
        elif tag in {"img", "source", "video", "audio", "iframe", "picture"}:
            self.assets.append({"tag": tag, "src": a.get("src"), "srcset": a.get("srcset")})
        elif tag == "form":
            self.forms.append({"method": a.get("method"), "action": a.get("action")})
        elif tag == "meta":
            self.metadata.append({"name": a.get("name"), "property": a.get("property"),
                                  "http_equiv": a.get("http-equiv")})

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag == "script":
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._script_depth = max(0, self._script_depth - 1)

    def handle_data(self, data: str) -> None:
        if self._script_depth:
            self._inline_script_chars += len(data)
            if self._feature_config is not None:
                for feature, signals in scan_feature_signals(data, self._feature_config).items():
                    self.inline_feature_signals.setdefault(feature, set()).update(signals)

    def summary(self) -> dict:
        return {
            "tag_counts": dict(self.tags), "scripts": self.scripts,
            "stylesheets": self.styles, "assets": self.assets, "forms": self.forms,
            "other_links": self.links, "metadata": self.metadata,
            "inline_handlers": dict(self.inline_handlers),
            "inline_script_characters": self._inline_script_chars,
            "inline_feature_signals": {
                key: sorted(value) for key, value in sorted(self.inline_feature_signals.items())
            }
        }


def category(name: str) -> str:
    return CATEGORIES.get(PurePosixPath(name).suffix.lower(), "other")


def scan_feature_signals(text: str, config: dict) -> dict[str, list[str]]:
    """Return only fixed signal category labels; discard all matched source text."""
    found = {}
    for feature in config["features"]:
        hits = [tag for tag, pattern in feature["signals"].items()
                if re.search(pattern, text, flags=re.I)]
        if hits:
            found[feature["id"]] = hits
    return found


def scan_text(name: str, contents: bytes) -> dict:
    text = contents.decode("utf-8", errors="replace")
    kind = category(name)
    if kind == "html":
        parser = PageParser(load_json(ROOT / "queues/static_profiles.json"))
        parser.feed(text)
        parser.close()
        return parser.summary()
    if kind == "stylesheet":
        return {"media_rules": len(re.findall(r"@media\b", text, flags=re.I)),
                "imports": len(re.findall(r"@import\b", text, flags=re.I)),
                "font_faces": len(re.findall(r"@font-face\b", text, flags=re.I)),
                "custom_properties": len(re.findall(r"--[a-zA-Z][\w-]*\s*:", text))}
    if kind == "script":
        feature_config = load_json(ROOT / "queues/static_profiles.json")
        return {"feature_signals": scan_feature_signals(text, feature_config),
                "static_imports": len(re.findall(r"\bimport\s*(?:\(|[\"'{*])", text)),
                "fetch_references": len(re.findall(r"\bfetch\s*\(", text)),
                "storage_references": len(re.findall(r"\b(?:localStorage|sessionStorage|indexedDB)\b", text)),
                "event_listeners": len(re.findall(r"\baddEventListener\s*\(", text))}
    return {}


def safe_entry(name: str) -> bool:
    p = PurePosixPath(name)
    return bool(name) and not name.startswith(("/", "\\")) and "\\" not in name and ":" not in name and ".." not in p.parts


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_capture(path: Path) -> dict:
    """No extraction, subprocesses, script execution or network operations."""
    if not path.is_file():
        raise ValueError("Input must be an existing regular file")
    resolved = path.resolve()
    if resolved.is_relative_to(ROOT.resolve()):
        raise ValueError("Capture input must be located outside this repository")
    if resolved.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("Capture exceeds supported size limit")

    items: list[dict] = []
    if resolved.suffix.lower() == ".zip":
        with zipfile.ZipFile(resolved) as archive:
            infos = [i for i in archive.infolist() if not i.is_dir()]
            if len(infos) > MAX_MEMBER_COUNT:
                raise ValueError("Capture has too many archive members")
            total = 0
            for info in infos:
                if not safe_entry(info.filename):
                    raise ValueError("Capture contains an unsafe archive entry")
                mode = info.external_attr >> 16
                if stat.S_ISLNK(mode):
                    raise ValueError("Capture contains a symbolic link")
                total += info.file_size
                if total > MAX_TOTAL_UNCOMPRESSED:
                    raise ValueError("Capture exceeds uncompressed size limit")
                if info.file_size > 0 and info.file_size / max(info.compress_size, 1) > 1000:
                    raise ValueError("Capture contains an extreme compression ratio")
            for info in infos:
                entry = {"path": info.filename, "size": info.file_size,
                         "category": category(info.filename), "crc32": f"{info.CRC:08x}"}
                if entry["category"] in {"html", "script", "stylesheet"} and info.file_size <= MAX_SCAN_BYTES:
                    with archive.open(info) as stream:
                        entry["observations"] = scan_text(info.filename, stream.read(MAX_SCAN_BYTES + 1))
                elif entry["category"] in {"html", "script", "stylesheet"}:
                    entry["scan_limited"] = True
                items.append(entry)
        scope = "saved_archive"
    elif resolved.suffix.lower() in {".html", ".htm", ".xhtml"}:
        entry = {"path": resolved.name, "size": resolved.stat().st_size, "category": "html"}
        if resolved.stat().st_size <= MAX_SCAN_BYTES:
            entry["observations"] = scan_text(resolved.name, resolved.read_bytes())
        else:
            entry["scan_limited"] = True
        items.append(entry)
        scope = "saved_page"
    else:
        raise ValueError("Capture must be a ZIP archive or saved HTML file")
    counts = Counter(item["category"] for item in items)
    return {
        "private_evidence": True, "capture_sha256": file_digest(resolved),
        "source_path": str(resolved), "capture_scope": scope, "file_count": len(items),
        "categories": dict(sorted(counts.items())), "files": items,
        "limits": {"scan_bytes_per_text_file": MAX_SCAN_BYTES}
    }


def queue_specimen(slug: str, origin: str) -> None:
    if not slug_ok(slug):
        raise ValueError("Specimen ID must be a lowercase slug (2-48 characters)")
    origin = public_origin(origin)
    path = ROOT / "specimens/index.json"
    index = load_json(path)
    if any(item["id"] == slug for item in index["specimens"]):
        raise ValueError("Specimen ID already exists")
    if any(item["origin"] == origin for item in index["specimens"]):
        raise ValueError("Origin already has a specimen; use the existing ID")
    index["specimens"].append({"id": slug, "origin": origin, "status": "queued",
                               "current_version": 0, "versions": []})
    index["specimens"].sort(key=lambda item: item["id"])
    save_json(path, index)



def deep_capture_eligible(inventory: dict, config: dict) -> bool:
    """Large or source-rich archives need a persistent second research phase."""
    if inventory["capture_scope"] != "saved_archive":
        return False
    counts = inventory["categories"]
    threshold = config["trigger"]
    return (inventory["file_count"] >= threshold["min_archive_files"] or
            counts.get("script", 0) >= threshold["min_script_files"] or
            counts.get("stylesheet", 0) >= threshold["min_stylesheet_files"])


def spawn_deep_research(slug: str, version: int, inventory: dict, config: dict) -> list[dict]:
    if not deep_capture_eligible(inventory, config):
        return []
    prefix = f"{slug}-v{version:04d}-"
    selected = [p for p in config["profiles"]
                if set(p["requires"]).issubset(inventory["categories"])]
    ids = {p["id"]: prefix + "followup-deep-" + p["id"] for p in selected}
    tasks = []
    for p in selected:
        deps = []
        for dep in p["depends_on"]:
            if dep.startswith("base:"):
                deps.append(prefix + dep[5:])
            elif dep.startswith("deep:") and dep[5:] in ids:
                deps.append(ids[dep[5:]])
        tasks.append({
            "id": ids[p["id"]], "specimen_id": slug, "version": version,
            "profile": "followup", "queue": p["queue"], "title": p["title"],
            "status": "queued", "depends_on": deps or [prefix + "intake"],
            "notes": "Deep research contract: " + p["acceptance"]
        })
    return tasks


def available_static_kinds(inventory: dict) -> set[str]:
    kinds = set(inventory["categories"])
    if any(item["category"] == "html" and
           item.get("observations", {}).get("inline_script_characters", 0) > 0
           for item in inventory["files"]):
        kinds.add("script")
    return kinds


def candidate_static_features(inventory: dict, config: dict) -> list[str]:
    """Require all feature signal families in at least one captured script."""
    counts: Counter[str] = Counter()
    required = {f["id"]: set(f["signals"]) for f in config["features"]}
    for item in inventory["files"]:
        if item["category"] not in {"script", "html"}:
            continue
        observations = item.get("observations", {})
        label = ("feature_signals" if item["category"] == "script"
                 else "inline_feature_signals")
        for feature, hits in observations.get(label, {}).items():
            if feature in required and required[feature] <= set(hits):
                counts[feature] += 1
    # Large captures often vendor unrelated libraries; do not promote a
    # single lexical hit into a feature-specific task chain. Small sites
    # may legitimately ship all feature code in one JavaScript bundle.
    minimum = 2 if inventory["categories"].get("script", 0) >= 20 else 1
    return sorted(feature for feature, total in counts.items() if total >= minimum)


def spawn_static_research(slug: str, version: int, inventory: dict,
                          config: dict) -> list[dict]:
    """Schedule source tracing for any qualifying dump, not just large ZIPs."""
    prefix = f"{slug}-v{version:04d}-"
    available = available_static_kinds(inventory)
    selected = [p for p in config["profiles"] if set(p["requires"]) <= available]
    ids = {p["id"]: prefix + "followup-static-" + p["id"] for p in selected}
    tasks = []

    def dependency(dep: str, feature: str | None = None) -> str | None:
        if dep.startswith("base:"):
            return prefix + dep[5:]
        if dep.startswith("static:"):
            return ids.get(dep[7:])
        if dep.startswith("feature:") and feature is not None:
            return prefix + "followup-static-feature-" + feature + "-" + dep[8:]
        raise ValueError("Unsupported static research dependency")

    for p in selected:
        deps = [d for item in p["depends_on"] if (d := dependency(item))]
        tasks.append({
            "id": ids[p["id"]], "specimen_id": slug, "version": version,
            "profile": "followup", "queue": p["queue"], "title": p["title"],
            "status": "queued", "depends_on": deps or [prefix + "intake"],
            "notes": "Static implementation trace: " + p["acceptance"]
        })
    for feature in candidate_static_features(inventory, config):
        name = next(f["label"] for f in config["features"] if f["id"] == feature)
        for item in config["feature_tasks"]:
            deps = [d for ref in item["depends_on"]
                    if (d := dependency(ref, feature))]
            tasks.append({
                "id": prefix + "followup-static-feature-" + feature + "-" + item["id"],
                "specimen_id": slug, "version": version, "profile": "followup",
                "queue": item["queue"], "title": name + ": " + item["title"],
                "status": "queued", "depends_on": deps or [prefix + "intake"],
                "notes": ("Candidate feature inferred only from static signal vocabulary. "
                          "Confirm module ownership before closing. " + item["acceptance"])
            })
    return tasks


def process_specimen(slug: str, input_path: Path) -> int:
    index_path = ROOT / "specimens/index.json"
    index = load_json(index_path)
    specimen = next((s for s in index["specimens"] if s["id"] == slug), None)
    if specimen is None:
        raise ValueError("Queue the specimen before processing")
    inventory = inspect_capture(input_path)
    version = specimen["current_version"] + 1
    key = f"v{version:04d}"
    destination = ROOT / "specimens" / slug / key
    if destination.exists():
        raise ValueError("Version directory already exists; refusing overwrite")
    profiles = load_json(ROOT / "queues/profiles.json")["profiles"]
    task_path = ROOT / "queues/tasks.json"
    tasks_doc = load_json(task_path)
    task_ids = {p["id"]: f"{slug}-{key}-{p['id']}" for p in profiles}
    spawned = [
        {"id": task_ids[p["id"]], "specimen_id": slug, "version": version,
         "profile": p["id"], "queue": p["queue"], "title": p["title"],
         "status": "queued", "depends_on": [task_ids[d] for d in p["depends_on"]]}
        for p in profiles
    ]
    spawned.extend(spawn_deep_research(slug, version, inventory,
                                      load_json(ROOT / "queues/deep_profiles.json")))
    spawned.extend(spawn_static_research(slug, version, inventory,
                                        load_json(ROOT / "queues/static_profiles.json")))
    if {t["id"] for t in spawned} & {t["id"] for t in tasks_doc["tasks"]}:
        raise ValueError("Duplicate task identifiers")
    processed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    record = {
        "format_version": 1, "ontology_version": "1.0.0", "specimen_id": slug,
        "version": version, "capture_scope": inventory["capture_scope"],
        "processed_at": processed_at, "previous_version": version - 1 if version > 1 else None,
        "status": "processed", "coverage": {p["id"]: "pending" for p in profiles},
        "components": [], "relationships": [], "findings": [],
        "limitations": [
            "Saved files only; site scripts were not executed and no network calls were made.",
            "Server implementation, live behavior and completeness beyond capture scope remain unverified."
        ]
    }
    dossier = f"""# {slug} — {key}

Internal snapshot version: {version}. Source class: {inventory['capture_scope']}. Processed: {processed_at}.

## Capture scope and limitations

The source was inspected offline. No source archive or copied site file is stored in this repository. Findings have not yet been established; see the version's research tasks.

## Structure and navigation

Pending evidence review.

## Scripts and dependencies

Pending evidence review.

## Styling, typography and assets

Pending evidence review.

## Interactions, state and services

Pending evidence review.

## Accessibility, metadata, performance and security

Pending evidence review.

## Architecture and relationships

Pending evidence review.

## Comparison with previous capture

{"First captured version; no earlier baseline." if version == 1 else "Pending like-for-like comparison with the preceding internal capture version."}

## Evidence assessment and open questions

Pending. Mark unobserved runtime and server-side behavior as unknown instead of inferring it from a static snapshot.

## Publication review

Not reviewed. Source rights, technical identifiers, evidence classifications, and uncertainties must be checked before finalizing a dossier.
"""
    private_dir = WORKDIR / slug / key
    private_dir.mkdir(parents=True, exist_ok=False)
    save_json(private_dir / "inventory.json", inventory)
    save_json(destination / "record.json", record)
    (destination / "analysis.md").write_text(dossier, encoding="utf-8")
    tasks_doc["tasks"].extend(spawned)
    save_json(task_path, tasks_doc)
    specimen["current_version"] = version
    specimen["versions"].append(version)
    specimen["status"] = "processed"
    save_json(index_path, index)
    return version


def enqueue_static_for_current_version(slug: str, input_path: Path) -> int:
    """Add newly introduced static research to a previously processed capture.

    This does not create a fake new capture version or erase reviewed findings.
    A prior ignored inventory digest is checked when available; otherwise,
    a curated aggregate resource census must be consistent with the input.
    """
    index_path = ROOT / "specimens/index.json"
    index = load_json(index_path)
    specimen = next((s for s in index["specimens"] if s["id"] == slug), None)
    if specimen is None or specimen["current_version"] < 1:
        raise ValueError("A processed specimen version is required")
    version = specimen["current_version"]
    inventory = inspect_capture(input_path)
    prior_path = WORKDIR / slug / f"v{version:04d}" / "inventory.json"
    if prior_path.is_file():
        prior = load_json(prior_path)
        if prior["capture_sha256"] != inventory["capture_sha256"]:
            raise ValueError("Input does not match the original captured version")
    else:
        census_path = ROOT / "specimens" / slug / f"v{version:04d}" / "resource_inventory.json"
        if not census_path.is_file():
            raise ValueError("Original capture identity cannot be checked")
        census = load_json(census_path)["totals"]["captured_by_category"]
        if any(inventory["categories"].get(kind, 0) < count
               for kind, count in census.items()):
            raise ValueError("Capture differs from the published resource census")
    path = ROOT / "queues/tasks.json"
    tasks_doc = load_json(path)
    proposed = spawn_static_research(
        slug, version, inventory, load_json(ROOT / "queues/static_profiles.json"))
    existing = {task["id"] for task in tasks_doc["tasks"]}
    new = [task for task in proposed if task["id"] not in existing]
    if not new:
        return 0
    tasks_doc["tasks"].extend(new)
    save_json(path, tasks_doc)
    # A completed capture-specific research pass remains historically
    # documented, but new source research makes current review incomplete.
    record_path = ROOT / "specimens" / slug / f"v{version:04d}" / "record.json"
    record = load_json(record_path)
    if record["status"] == "reviewed":
        record["status"] = "researching"
        for section in ("scripts", "interaction", "state", "services",
                        "architecture", "review"):
            if record["coverage"].get(section) == "analyzed":
                record["coverage"][section] = "partial"
        save_json(record_path, record)
        specimen["status"] = "researching"
        save_json(index_path, index)
    return len(new)


def show_status() -> None:
    specimens = load_json(ROOT / "specimens/index.json")["specimens"]
    tasks = load_json(ROOT / "queues/tasks.json")["tasks"]
    summary = Counter(t["status"] for t in tasks)
    print(f"specimens={len(specimens)} versions={sum(len(s['versions']) for s in specimens)} tasks={len(tasks)}")
    print("task_status=" + json.dumps(dict(sorted(summary.items())), sort_keys=True))
    for item in specimens:
        print(f"{item['id']}: {item['status']} v{item['current_version']:04d}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline website research specimen manager")
    sub = parser.add_subparsers(dest="command", required=True)
    queue = sub.add_parser("queue", help="Queue a website identity")
    queue.add_argument("slug")
    queue.add_argument("--origin", required=True, help="Bare public DNS origin, without path or query")
    process = sub.add_parser("process", help="Process offline ZIP/HTML and create tasks")
    process.add_argument("slug")
    process.add_argument("--input", required=True, type=Path, help="Capture located outside the repository")
    backfill = sub.add_parser("enqueue-static", help="Reopen current capture for newly added static research")
    backfill.add_argument("slug")
    backfill.add_argument("--input", required=True, type=Path,
                          help="Original ZIP or HTML input, outside this repository")
    sub.add_parser("status", help="Display queued work summary")
    args = parser.parse_args()
    try:
        if args.command == "queue":
            queue_specimen(args.slug, args.origin)
            print("Specimen queued.")
        elif args.command == "process":
            version = process_specimen(args.slug, args.input)
            print(f"Capture processed as internal version v{version:04d}; research tasks queued.")
        elif args.command == "enqueue-static":
            count = enqueue_static_for_current_version(args.slug, args.input)
            print(f"Queued {count} new static-analysis tasks for the current version.")
        elif args.command == "status":
            show_status()
    except (ValueError, OSError, zipfile.BadZipFile, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
