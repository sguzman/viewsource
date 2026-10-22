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
            # Only explicitly allowlisted anonymous graph and structural metrics
            # are passed to the website. The full analysis file is not copied.
            visuals = {}
            phase3_path = ROOT / (base + "/phase3_analysis.json")
            if phase3_path.is_file():
                study = read(base + "/phase3_analysis.json")
                if study["specimen_id"] != item["id"] or study["version"] != number:
                    raise ValueError("Deep source study identity mismatch")
                graph = study["javascript_ast"]
                visuals["module_imports"] = {
                    "evidence_ref": "E2-041",
                    "static_edges": graph["mapped_static_import_edges"],
                    "target_bundle_count": graph["target_bundle_count"],
                    "sources": [{
                        "source": source,
                        "target_ranges": ranges,
                        "target_count": sum(high - low + 1 for low, high in ranges)
                    } for source, ranges in graph["source_to_target_ranges"].items()]
                }
                document = study["document"]
                visuals["landmarks"] = {
                    "evidence_ref": "E2-038",
                    "button_total": document["buttons"],
                    "closest_landmark_buttons": document["closest_landmark_buttons"],
                    "nav_inside_aside": document["nav_inside_aside"]
                }
                icon = study["icon_linkage"]
                visuals["icons"] = {
                    "evidence_ref": "E2-044",
                    "sprite_ordinal": icon["sprite_resource_ordinal"],
                    "matched_uses": icon["svg_uses_matching_symbol_id"],
                    "unique_symbols": icon["unique_sprite_symbols_referenced"]
                }
            css_study_path = ROOT / (base + "/phase4_css_analysis.json")
            if css_study_path.is_file():
                css_study = read(base + "/phase4_css_analysis.json")
                if css_study["specimen_id"] != item["id"] or css_study["version"] != number:
                    raise ValueError("CSS research identity mismatch")
                groups = css_study["tokens"]["families"]
                visuals["css_system"] = {
                    "evidence_refs": ["E2-048", "E2-049", "E2-050"],
                    "distinct_tokens": css_study["tokens"]["distinct_defined_names"],
                    "references": css_study["tokens"]["variable_reference_occurrences"],
                    "token_groups": [
                        {"name": key.replace("_", " "),
                         "distinct": value["distinct_definitions"],
                         "references": value["references"]}
                        for key, value in groups.items()
                    ],
                    "media_rule_occurrences": css_study["responsive"]["lexical_media_at_rules"],
                    "container_rule_occurrences": css_study["responsive"]["lexical_container_at_rules"],
                    "reduced_motion_rules": css_study["motion"]["reduced_motion_media_preludes"],
                    "keyframes": css_study["motion"]["keyframe_rule_occurrences"]
                }
            system_path = ROOT / (base + "/phase5_system_analysis.json")
            if system_path.is_file():
                report = read(base + "/phase5_system_analysis.json")
                if report["specimen_id"] != item["id"] or report["version"] != number:
                    raise ValueError("System report identity mismatch")
                api = report["js_ast"]["fixed_api_indicators"]
                co = report["js_ast"]["same_lexical_function_scope_cooccurrences"]
                budget = report["captured_resource_budget"]
                visuals["source_system"] = {
                    "evidence_refs": ["E2-053", "E2-054", "E2-055", "E2-059"],
                    "event_signals": [
                        {"label": "Listener registration", "count": api["listener_add_calls"]},
                        {"label": "Listener removal", "count": api["listener_remove_calls"]},
                        {"label": "Animation frame", "count": api["animation_frame_calls"]},
                        {"label": "Mutation observer", "count": api["mutation_observer_constructors"]},
                        {"label": "Resize observer", "count": api["resize_observer_constructors"]},
                        {"label": "Intersection observer", "count": api["intersection_observer_constructors"]}
                    ],
                    "state_signals": [
                        {"label": "Get item", "count": api["storage_get_item_calls"]},
                        {"label": "Set item", "count": api["storage_set_item_calls"]},
                        {"label": "Remove item", "count": api["storage_remove_item_calls"]},
                        {"label": "Channel", "count": api["broadcast_channel_constructors"]},
                        {"label": "Message channel", "count": api["message_channel_constructors"]},
                        {"label": "Post message", "count": api["post_message_calls"]},
                        {"label": "Worker", "count": api["worker_constructors"]}
                    ],
                    "network_signals": [
                        {"label": "Fetch", "count": api["fetch"]},
                        {"label": "Abort controller", "count": api["abort_controller_constructors"]},
                        {"label": "Stream reader", "count": api["stream_reader_calls"]},
                        {"label": "Text decoder", "count": api["text_decoder_constructors"]},
                        {"label": "WebSocket", "count": api["websocket_constructors"]},
                        {"label": "Peer connection", "count": api["peer_connection_constructors"]}
                    ],
                    "lexical_scopes": {
                        "fetch_and_stream": co["fetch_and_stream"],
                        "fetch_and_abort": co["fetch_and_abort"]
                    },
                    "bytes": {
                        "scripts": budget["scripts"]["bytes"],
                        "css": budget["styles"]["bytes"],
                        "fonts": budget["fonts"]["bytes"],
                        "images": budget["images"]["bytes"]
                    }
                }
            technology_path = ROOT / (base + "/technology_inventory.json")
            if technology_path.is_file():
                study = read(base + "/technology_inventory.json")
                if study["specimen_id"] != item["id"] or study["version"] != number:
                    raise ValueError("Technology study identity mismatch")
                allowed_strength = {"strong", "likely", "indicator"}
                items = []
                for item_tech in study["technologies"]:
                    if item_tech["confidence"] not in allowed_strength:
                        raise ValueError("Unsupported evidence confidence")
                    items.append({
                        "id": item_tech["id"], "name": item_tech["name"],
                        "category": item_tech["category"],
                        "confidence": item_tech["confidence"],
                        "role": item_tech["role"],
                        "evidence": item_tech["evidence"],
                        "observations": [{
                            "marker": m["marker"], "matches": m["matches"], "files": m["files"]
                        } for m in item_tech["observations"]],
                        "note": item_tech["note"]
                    })
                page_map = study["page_map"]
                visuals["technology"] = {
                    "evidence_ref": "E2-064",
                    "technologies": items,
                    "unresolved": [{"technology": x["technology"], "reason": x["reason"]}
                                   for x in study["unresolved"]]
                }
                visuals["page_map"] = {
                    "evidence_ref": "E2-065",
                    "nodes": [{
                        "id": n["id"], "title": n["title"], "kind": n["kind"],
                        "description": n["description"], "counts": n["counts"],
                        "evidence": n["evidence"]
                    } for n in page_map["nodes"]],
                    "observed_control_categories": page_map["observed_control_categories"],
                    "note": page_map["note"]
                }
            chat_signals_path = ROOT / (base + "/chat_source_signals.json")
            if chat_signals_path.is_file():
                signals = read(base + "/chat_source_signals.json")
                if signals["specimen_id"] != item["id"] or signals["version"] != number:
                    raise ValueError("Chat source signal identity mismatch")
                visuals["chat_source_signals"] = {
                    "evidence_refs": ["E2-066", "E2-067", "E2-068", "E2-069"],
                    "scope": "saved_archive",
                    "dom_controls": {
                        "document": signals["dom_footprint"]["document"],
                        "features": [
                            {"category": x["category"], "count": x["count"],
                             "nearest_region": x.get("nearest_region", "multiple")}
                            for x in signals["dom_footprint"]["features"]
                        ],
                        "caveat": signals["dom_footprint"]["caveat"]
                    },
                    "summary": [
                        {"label": "Conversation identity indicators",
                         "count": signals["identifier_categories"]["conversation_like"]["files"]},
                        {"label": "Message identity indicators",
                         "count": signals["identifier_categories"]["message_like"]["files"]},
                        {"label": "Parent reference indicators",
                         "count": signals["identifier_categories"]["parent_like"]["files"]},
                        {"label": "Branch-related indicators",
                         "count": signals["identifier_categories"]["branch_like"]["files"]},
                        {"label": "Stream-related indicators",
                         "count": signals["identifier_categories"]["stream_like"]["files"]}
                    ],
                    "object_relationships": [
                        {"label": key.replace("_", " "), "count": value["objects"]}
                        for key, value in signals["object_literal_pairs"].items()
                    ],
                    "function_relationships": [
                        {"label": key.replace("_", " "), "count": value["functions"]}
                        for key, value in signals["lexical_function_pairs"].items()
                    ]
                }
            feature_queue_path = ROOT / "queues/chat_research.json"
            if feature_queue_path.is_file():
                research = read("queues/chat_research.json")
                if research["specimen_id"] == item["id"] and research["version"] == number:
                    visuals["feature_research"] = {
                        "policy": research["policy"],
                        "tasks": [
                            {"id": task["id"], "title": task["title"],
                             "status": task["status"], "scope": task["scope"],
                             "depends_on": task["depends_on"],
                             "acceptance": task["acceptance"],
                             "evidence_refs": task["evidence_refs"]}
                            for task in research["tasks"]
                        ]
                    }
            feature_path = ROOT / (base + "/chat-interaction.graph.json")
            if feature_path.is_file():
                feature = read(base + "/chat-interaction.graph.json")
                if feature["specimen_id"] != item["id"] or feature["version"] != number:
                    raise ValueError("Feature graph identity mismatch")
                # Export only authored, allowlisted ontology graph fields.
                graph_public = {
                    "format_version": 1, "feature_id": feature["feature_id"],
                    "title": feature["title"], "model_status": feature["model_status"],
                    "source_scope": feature["source_scope"],
                    "technology_links": feature["technology_links"],
                    "surfaces": feature["surfaces"],
                    "entities": feature["entities"],
                    "domain_relations": feature["domain_relations"],
                    "machines": feature["machines"],
                    "events": feature["events"],
                    "transitions": feature["transitions"],
                    "branch_model": feature["branch_model"],
                    "open_questions": feature["open_questions"],
                    "limitations": feature["limitations"]
                }
                filename = f"{item['id']}-v{number:04d}-{feature['feature_id']}.json"
                graph_public["json_path"] = "./data/features/" + filename
                visuals["feature_graph"] = graph_public
            inventory = read(base + "/resource_inventory.json") if (ROOT / (base + "/resource_inventory.json")).is_file() else {}
            totals = inventory.get("totals", {})
            catalog["versions"].append({
                "specimen_id": item["id"], "version": number,
                "capture_scope": record["capture_scope"], "status": record["status"],
                "processed_at": record["processed_at"],
                "coverage": record["coverage"], "components": components,
                "relationships": relationships, "findings": findings,
                "tasks": scoped_tasks, "chapters": chapters, "visuals": visuals,
                "limitations": record["limitations"],
                "resource_summary": {
                    "captured": totals.get("external_references", 0),
                    "by_category": totals.get("captured_by_category", {}),
                    "missing": totals.get("missing_reported", 0)
                }
            })
    out.mkdir(parents=True, exist_ok=True)
    (out / "data").mkdir(exist_ok=True)
    (out / "data" / "features").mkdir(exist_ok=True)
    for version in catalog["versions"]:
        graph = version.get("visuals", {}).get("feature_graph")
        if graph:
            filename = graph["json_path"].split("/")[-1]
            (out / "data" / "features" / filename).write_text(
                json.dumps(graph, ensure_ascii=True, indent=2) + "\n", encoding="utf-8"
            )
    for name in ("index.html", "app.css", "explorer.js", "chat-graph.js", "app.js"):
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
