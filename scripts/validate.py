#!/usr/bin/env python3
"""Stdlib validation of Viewsource's version, ontology, queue and gallery references."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
import sys

from validate_feature_graph import validate_extensions
from validate_feature_research import validate_feature_research

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r"^[a-z][a-z0-9-]{1,47}$")
STATES = {"queued", "in_progress", "blocked", "not_observable", "done"}
EVIDENCE_CLASSES = {"observed_static", "inferred_static", "observed_live", "external_source", "unknown"}
COVERAGE = {"pending", "partial", "analyzed", "not_observable"}


def read(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def validate() -> list[str]:
    errors = []
    def require(condition: bool, description: str) -> None:
        if not condition:
            errors.append(description)

    manifest = read("tarium.json")
    require(manifest["project"] == "viewsource", "Manifest project identity")
    require(manifest["membership"] == "unregistered", "Membership is not centrally authorized here")
    for group in ("ontology", "gallery"):
        for path in manifest[group].values():
            require((ROOT / path).is_file(), f"Manifest missing resource: {path}")

    model = read("ontology/ontology.json")
    require(model["ontology_version"] == "1.0.0", "Unexpected ontology version")
    for extension in ("technology_inventory", "feature_graph"):
        artifact = model.get("extension_artifacts", {}).get(extension, {})
        require(artifact.get("format_version") == 1 and (Path(__file__).resolve().parents[1] / artifact.get("schema", "__missing__")).is_file(),
                f"Missing or invalid ontology extension: {extension}")
    kinds = model["component_kinds"]
    relations = model["relations"]
    require(len(kinds) == len(set(kinds)), "Duplicate component kinds")
    require(len(relations) == len(set(relations)), "Duplicate relation kinds")

    profiles = read("queues/profiles.json")["profiles"]
    ids = [p["id"] for p in profiles]
    require(len(ids) == len(set(ids)), "Duplicate task profile")
    profile_by_id = {p["id"]: p for p in profiles}
    for p in profiles:
        require(p["queue"] and p["title"], f"Empty profile details: {p['id']}")
        for dep in p["depends_on"]:
            require(dep in profile_by_id and dep != p["id"], f"Invalid profile dependency: {p['id']} -> {dep}")
    def visits(node: str, seen: set[str], visiting: set[str]) -> None:
        if node in visiting:
            errors.append("Cyclic research profile dependency")
            return
        if node in seen:
            return
        visiting.add(node)
        for dep in profile_by_id[node]["depends_on"]:
            if dep in profile_by_id:
                visits(dep, seen, visiting)
        visiting.remove(node)
        seen.add(node)
    seen = set()
    for profile in ids:
        visits(profile, seen, set())

    specimens = read("specimens/index.json")["specimens"]
    require(len({s["id"] for s in specimens}) == len(specimens), "Duplicate specimen IDs")
    require(len({s["origin"] for s in specimens}) == len(specimens), "Duplicate specimen origins")
    require([s["id"] for s in specimens] == sorted(s["id"] for s in specimens), "Specimens must be sorted")
    by_specimen = {s["id"]: s for s in specimens}
    record_paths = set()
    for specimen in specimens:
        slug = specimen["id"]
        require(bool(SLUG.fullmatch(slug)) and not slug.endswith("-"), f"Invalid specimen slug: {slug}")
        versions = specimen["versions"]
        require(versions == list(range(1, len(versions) + 1)), f"Noncontiguous versions: {slug}")
        require(specimen["current_version"] == len(versions), f"Incorrect current version: {slug}")
        require(specimen["status"] in {"queued", "processed", "researching", "reviewed"}, f"Bad specimen status: {slug}")
        for version in versions:
            directory = f"specimens/{slug}/v{version:04d}"
            record_paths.add(directory + "/record.json")
            require((ROOT / directory / "analysis.md").is_file(), f"Missing dossier: {directory}")
            if not (ROOT / directory / "record.json").is_file():
                errors.append(f"Missing version record: {directory}")
                continue
            record = read(directory + "/record.json")
            require(record["format_version"] == 1, f"Record format: {directory}")
            require(record["ontology_version"] == model["ontology_version"], f"Record ontology version: {directory}")
            require(record["specimen_id"] == slug and record["version"] == version, f"Version ID mismatch: {directory}")
            require(record["previous_version"] == (version - 1 if version > 1 else None), f"Previous version mismatch: {directory}")
            require(record["capture_scope"] in {"saved_page", "saved_archive"}, f"Invalid capture scope: {directory}")
            require(record["status"] in {"processed", "researching", "reviewed"}, f"Invalid record status: {directory}")
            require(set(record["coverage"]) == set(ids), f"Coverage keys do not match profiles: {directory}")
            require(set(record["coverage"].values()) <= COVERAGE, f"Invalid coverage: {directory}")
            components = record["components"]
            component_ids = {c["id"] for c in components}
            require(len(component_ids) == len(components), f"Repeated component ID: {directory}")
            for component in components:
                require(component["kind"] in kinds, f"Unknown component type: {directory}")
                require(isinstance(component["properties"], dict), f"Invalid component properties: {directory}")
                check_evidence(component["evidence"], require, directory)
            for relation in record["relationships"]:
                require(relation["from"] in component_ids and relation["to"] in component_ids, f"Dangling component relation: {directory}")
                require(relation["predicate"] in relations, f"Invalid relation predicate: {directory}")
                check_evidence(relation["evidence"], require, directory)
            findings = record["findings"]
            require(len({f["id"] for f in findings}) == len(findings), f"Duplicate finding IDs: {directory}")
            for finding in findings:
                check_evidence(finding["evidence"], require, directory)
            validate_extensions(require, slug, version)

    disk_records = {p.relative_to(ROOT).as_posix() for p in (ROOT / "specimens").glob("*/v*/record.json")}
    require(disk_records == record_paths, "Unregistered version record or missing record")

    tasks = read("queues/tasks.json")["tasks"]
    tasks_by_id = {t["id"]: t for t in tasks}
    require(len(tasks_by_id) == len(tasks), "Duplicate task IDs")
    task_groups = Counter((t["specimen_id"], t["version"], t["profile"]) for t in tasks)
    for t in tasks:
        name = t["specimen_id"]
        ver = t["version"]
        require(name in by_specimen and ver in by_specimen.get(name, {}).get("versions", []), f"Task missing specimen/version: {t['id']}")
        require(t["status"] in STATES, f"Invalid task state: {t['id']}")
        if t["status"] == "done":
            refs = t.get("evidence_refs", [])
            require(bool(refs), f"Completed task lacks evidence refs: {t['id']}")
            require(len(refs) == len(set(refs)), f"Duplicate task evidence refs: {t['id']}")
            record_path = ROOT / "specimens" / name / f"v{ver:04d}" / "record.json"
            if record_path.is_file():
                evidence_ids = {
                    f["evidence"].get("evidence_ref")
                    for f in read(f"specimens/{name}/v{ver:04d}/record.json")["findings"]
                }
                require(set(refs) <= evidence_ids, f"Completed task has ungrounded evidence ref: {t['id']}")

        if t["profile"] == "followup":
            require(t["id"].startswith(f"{name}-v{ver:04d}-followup-"), f"Bad followup task ID: {t['id']}")
            require(t["queue"] in {p["queue"] for p in profiles}, f"Unknown followup queue: {t['id']}")
            require(bool(t.get("notes")), f"Unscoped followup task: {t['id']}")
        else:
            require(t["profile"] in profile_by_id, f"Unknown task profile: {t['id']}")
            require(t["id"] == f"{name}-v{ver:04d}-{t['profile']}", f"Bad task ID: {t['id']}")
            if t["profile"] in profile_by_id:
                profile = profile_by_id[t["profile"]]
                require(t["queue"] == profile["queue"], f"Queue mismatch: {t['id']}")
                expected = {f"{name}-v{ver:04d}-{dep}" for dep in profile["depends_on"]}
                require(set(t["depends_on"]) == expected, f"Dependency mismatch: {t['id']}")
        for dep in t["depends_on"]:
            require(dep in tasks_by_id, f"Dangling task dependency: {t['id']}")
    for specimen in specimens:
        for version in specimen["versions"]:
            for profile in ids:
                require(task_groups[(specimen["id"], version, profile)] == 1, f"Missing profile task: {specimen['id']} v{version} {profile}")

    # Ensure a reviewed current version is synchronized with its specimen
    # status and that the research queue is genuinely terminal.
    for specimen in specimens:
        if not specimen["versions"]:
            continue
        slug = specimen["id"]
        latest = specimen["current_version"]
        record = read(f"specimens/{slug}/v{latest:04d}/record.json")
        require((specimen["status"] == "reviewed") == (record["status"] == "reviewed"),
                f"Specimen review status mismatch: {slug}")
        if record["status"] == "reviewed":
            require(all(value in {"analyzed", "not_observable"} for value in record["coverage"].values()),
                    f"Reviewed version contains incomplete coverage: {slug}")
            related = [t for t in tasks if t["specimen_id"] == slug and t["version"] == latest]
            require(all(t["status"] in {"done", "not_observable"} for t in related),
                    f"Reviewed version contains unfinished tasks: {slug}")

    # Optional sanitized resource inventory; captures that have only just been
    # processed may not have reached the detailed inventory research phase.
    for specimen in specimens:
        for version in specimen["versions"]:
            slug = specimen["id"]
            reference = ROOT / "specimens" / slug / f"v{version:04d}" / "resource_inventory.json"
            if not reference.exists():
                continue
            doc = read(str(reference.relative_to(ROOT)))
            require(doc.get("format_version") in {1, 2} and doc.get("specimen_id") == slug and doc.get("version") == version,
                    f"Resource inventory identity mismatch: {reference}")
            entries = doc.get("resources", [])
            require(len({row["id"] for row in entries}) == len(entries), f"Duplicate resource inventory ID: {reference}")
            require(doc.get("totals", {}).get("external_references") == len(entries),
                    f"Resource inventory count mismatch: {reference}")
            for row in entries:
                require(bool(re.fullmatch(r"R-[A-Z]+-[0-9]{3}", row["id"])), f"Invalid resource ordinal: {reference}")
                if doc["format_version"] == 1:
                    require(row["content_available"] is False, f"Resource content unexpectedly published: {reference}")
                    require(set(row) == {"id","category","ordinal","source_class","content_available","analysis_status","role"},
                            f"Unreviewed resource fields: {reference}")
                    require(row["source_class"] in {"capture_relative","same_origin_absolute"},
                            f"Unsupported resource origin class: {reference}")
                else:
                    permitted = {"id","category","ordinal","format","bytes","available_in_capture","content_committed","analysis_status"}
                    optional_fields = {"code_indicators","style_metrics"}
                    require(permitted <= set(row) and set(row) <= permitted | optional_fields,
                            f"Unreviewed v2 resource fields: {reference}")
                    require(set(row.get("code_indicators", [])) <= set(doc.get("code_indicator_vocabulary", [])),
                            f"Unrecognized static code indicator: {reference}")
                    require(set(row.get("style_metrics", {})) <= set(doc.get("style_metric_vocabulary", [])),
                            f"Unrecognized static CSS metric: {reference}")
                    require(all(isinstance(v, int) and v >= 0 for v in row.get("style_metrics", {}).values()),
                            f"Invalid CSS metric values: {reference}")
                    require(row["available_in_capture"] is True and row["content_committed"] is False,
                            f"Resource source publication prohibited: {reference}")
                    require(row["category"] in {"script","stylesheet","font","image","html"},
                            f"Invalid resource category: {reference}")
                    require(isinstance(row["bytes"], int) and row["bytes"] >= 0,
                            f"Invalid resource byte count: {reference}")
            if doc["format_version"] == 2:
                require(sum(doc["totals"]["captured_by_category"].values()) == len(entries),
                        f"Capture resource count mismatch: {reference}")
                require(sum(doc["totals"]["bytes_by_category"].values()) == doc["totals"]["bytes_captured"],
                        f"Capture resource bytes mismatch: {reference}")
                require(sum(row["bytes"] for row in entries) == doc["totals"]["bytes_captured"],
                        f"Per-resource bytes do not sum to capture total: {reference}")
                for k, v in doc.get("code_indicators", {}).items():
                    if k in doc.get("code_indicator_vocabulary", []):
                        require(sum(k in row.get("code_indicators", []) for row in entries) == v["asset_files"],
                                f"Code indicator count mismatch: {reference}")
                for k, v in doc.get("stylesheet_indicators", {}).items():
                    if k in doc.get("style_metric_vocabulary", []):
                        require(sum(row.get("style_metrics", {}).get(k, 0) for row in entries) == v,
                                f"Stylesheet indicator count mismatch: {reference}")

    # Optional source-level analysis from a privacy-cleared ZIP inventory.
    # The compact graph records ordinal textual references, NOT executable imports.
    for specimen in specimens:
        slug = specimen["id"]
        for version in specimen["versions"]:
            path = f"specimens/{slug}/v{version:04d}/source_analysis.json"
            if not (ROOT / path).is_file():
                continue
            study = read(path)
            require(study.get("format_version") == 1 and study.get("specimen_id") == slug and study.get("version") == version,
                    f"Source analysis identity mismatch: {path}")
            graph = study.get("javascript", {}).get("reference_graph", {})
            edges = set()
            for source, ranges in graph.get("source_to_target_ranges", {}).items():
                require(bool(re.fullmatch(r"R-JS-[0-9]{3}", source)), f"Invalid source ordinal: {path}")
                for bounds in ranges:
                    require(len(bounds) == 2 and all(isinstance(n, int) for n in bounds) and
                            1 <= bounds[0] <= bounds[1] <= study["javascript"]["captured_files"],
                            f"Invalid target ordinal range: {path}")
                    for ordinal in range(bounds[0], bounds[1] + 1):
                        edges.add((source, ordinal))
            require(graph.get("pairs") == len(edges), f"Source graph pair count mismatch: {path}")
            require(graph.get("source_bundles") == len({src for src, _ in edges}),
                    f"Source graph source count mismatch: {path}")
            require(graph.get("target_bundles") == len({dst for _, dst in edges}),
                    f"Source graph target count mismatch: {path}")
            require(graph.get("mentions", 0) >= len(edges), f"Source graph mentions inconsistent: {path}")
            require(study.get("methodology", {}).get("privacy") and study.get("limitations"),
                    f"Missing source analysis privacy or uncertainty caveats: {path}")
            require(all(isinstance(row["files"], int) and row["files"] >= 0
                        for row in study["javascript"].get("syntax_indicators", {}).values()),
                    f"Invalid source analysis syntax counts: {path}")
            require(sum(study["fonts"]["file_counts_by_family"].values()) == study["fonts"]["total_files"],
                    f"Font count mismatch: {path}")


    # Reviewed ZIP studies may publish a manually checked, aggregate-only
    # static deep-analysis report. Do not allow raw code or captured strings.
    for specimen in specimens:
        slug = specimen["id"]
        for version in specimen["versions"]:
            path = f"specimens/{slug}/v{version:04d}/deep_analysis.json"
            if not (ROOT / path).is_file():
                continue
            report = read(path)
            require(report.get("format_version") == 1 and report.get("specimen_id") == slug
                    and report.get("version") == version and report.get("source_scope") == "saved_archive",
                    f"Deep analysis identity invalid: {path}")
            require(report.get("limitations") and report.get("method"),
                    f"Deep analysis has no scoped methodology or limits: {path}")
            require(report.get("network", {}).get("observed_requests") == 0
                    and report.get("network", {}).get("remote_destinations_published") == 0,
                    f"Unreviewed network data publication: {path}")
            require(report.get("persistence", {}).get("storage_keys_published") == 0,
                    f"Unreviewed local storage data publication: {path}")
            require(report.get("security", {}).get("session_values_published") is False,
                    f"Unreviewed session material publication: {path}")
            require(report.get("evolution", {}).get("source_scope_difference", {})
                    .get("verified_site_product_changes") == 0,
                    f"Unverified site product changes claimed: {path}")

    errors.extend(validate_feature_research())

    gallery = read("gallery/index.json")
    require(gallery["format_version"] == 1, "Gallery format")
    require(len({item["id"] for item in gallery["entries"]}) == len(gallery["entries"]), "Duplicate gallery item")
    for item in gallery["entries"]:
        require(item["specimen_id"] in by_specimen, f"Gallery entry missing specimen: {item['id']}")
        require((ROOT / item["path"]).is_file(), f"Gallery entry points to missing artifact: {item['id']}")
        require(bool(item.get("provenance")) and bool(item.get("license")), f"Gallery rights missing: {item['id']}")
    return errors


def check_evidence(e: dict, require, origin: str) -> None:
    require(e["evidence_class"] in EVIDENCE_CLASSES, f"Invalid evidence class: {origin}")
    require(e["confidence"] in {"high", "medium", "low", "unknown"}, f"Invalid confidence: {origin}")
    if e["evidence_class"] not in {"unknown"}:
        require(bool(e.get("evidence_ref")), f"Missing evidence reference: {origin}")
    if e["evidence_class"] == "unknown":
        require(e["confidence"] == "unknown", f"Unknown class must have unknown confidence: {origin}")


def main() -> int:
    try:
        issues = validate()
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        return 1
    if issues:
        for issue in sorted(set(issues)):
            print(issue, file=sys.stderr)
        return 1
    print("Viewsource ontology, specimen references, gallery and research task graph: valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
