#!/usr/bin/env python3
"""Build the public, privacy-bounded Viewsource specimen atlas.

Only allowlisted fields from already-public research are exported. Raw captures,
private inventories, source strings and user identifiers are never read.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


def read(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def build(out: Path) -> dict:
    index = read("specimens/index.json")["specimens"]
    tasks = read("queues/tasks.json")["tasks"]
    editorial = read("site/story.json")
    catalog = {"format_version": 1, "specimens": [], "versions": []}
    for item in index:
        catalog["specimens"].append({
            "id": item["id"], "origin": item["origin"], "versions": item["versions"],
            "current_version": item["current_version"], "status": item["status"]
        })
        for number in item["versions"]:
            base = f"specimens/{item['id']}/v{number:04d}"
            record = read(base + "/record.json")
            if record["specimen_id"] != item["id"] or record["version"] != number:
                raise ValueError("Mismatched specimen identity in reviewed research")
            components = [{
                "id": c["id"], "kind": c["kind"], "name": c["name"],
                "description": c["description"][:550],
                "evidence_ref": c["evidence"].get("evidence_ref"),
                "evidence_class": c["evidence"]["evidence_class"]
            } for c in record["components"]]
            relationships = [{
                "from": edge["from"], "to": edge["to"], "predicate": edge["predicate"],
                "evidence_ref": edge["evidence"].get("evidence_ref")
            } for edge in record["relationships"]]
            findings = [{
                "id": f["id"], "statement": f["statement"][:1100],
                "ref": f["evidence"].get("evidence_ref"), "class": f["evidence"]["evidence_class"],
                "confidence": f["evidence"]["confidence"]
            } for f in record["findings"]]
            scoped_tasks = [{
                "id": t["id"], "title": t["title"], "queue": t["queue"],
                "status": t["status"], "depends_on": t["depends_on"],
                "notes": t.get("notes", "")[:450]
            } for t in tasks if t["specimen_id"] == item["id"] and t["version"] == number]
            chapters = []
            if editorial["specimen_id"] == item["id"] and editorial["version"] == number:
                chapters = editorial["chapters"]
                refs = {f["ref"] for f in findings}
                for chapter in chapters:
                    if not set(chapter["evidence"]) <= refs:
                        raise ValueError(f"Story chapter has unsupported evidence: {chapter['id']}")
            inventory = read(base + "/resource_inventory.json") if (ROOT / (base + "/resource_inventory.json")).is_file() else {}
            totals = inventory.get("totals", {})
            catalog["versions"].append({
                "specimen_id": item["id"], "version": number,
                "capture_scope": record["capture_scope"], "status": record["status"],
                "processed_at": record["processed_at"],
                "coverage": record["coverage"], "components": components,
                "relationships": relationships, "findings": findings,
                "tasks": scoped_tasks, "chapters": chapters,
                "limitations": record["limitations"],
                "resource_summary": {
                    "captured": totals.get("external_references", 0),
                    "by_category": totals.get("captured_by_category", {}),
                    "missing": totals.get("missing_reported", 0)
                }
            })
    out.mkdir(parents=True, exist_ok=True)
    (out / "data").mkdir(exist_ok=True)
    for name in ("index.html", "app.css", "app.js"):
        shutil.copyfile(SITE / name, out / name)
    (out / ".nojekyll").write_text("", encoding="utf-8")
    (out / "data/catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=True, separators=(",", ":")) + "\n",
        encoding="utf-8"
    )
    return catalog


def main():
    parser = argparse.ArgumentParser(description="Build static research atlas from curated public records")
    parser.add_argument("--out", type=Path, default=ROOT / "_site")
    args = parser.parse_args()
    catalog = build(args.out)
    print(f"Atlas built: {len(catalog['specimens'])} specimens, {len(catalog['versions'])} versions")


if __name__ == "__main__":
    main()
