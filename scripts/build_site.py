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
            capability_path = ROOT / (base + "/chat_capability_matrix.json")
            if capability_path.is_file():
                matrix = read(base + "/chat_capability_matrix.json")
                if matrix["specimen_id"] != item["id"] or matrix["version"] != number:
                    raise ValueError("Chat capability matrix identity mismatch")
                visuals["chat_capabilities"] = {
                    "entries": [{
                        "id": x["id"], "label": x["label"],
                        "static_refs": x["static_refs"],
                        "documented_action": x["documented_action"],
                        "candidate_events": x["candidate_events"],
                        "candidate_relations": x["candidate_relations"],
                        "runtime_status": x["runtime_status"],
                        "next_experiment": x["next_experiment"]
                    } for x in matrix["capabilities"]]
                }
            implementation_path = ROOT / (base + "/chat_static_impl_trace.json")
            if implementation_path.is_file():
                study = read(base + "/chat_static_impl_trace.json")
                if (study["specimen_id"] != item["id"] or study["version"] != number
                        or study["server_contract_verified"] is not False):
                    raise ValueError("Static chat trace scope mismatch")
                visuals["chat_static_impl_trace"] = {
                    "asset_files_parsed": study["asset_files_parsed"],
                    "match_count": study["match_count"],
                    "matched_functions": study["matched_functions"],
                    "patterns": study["patterns"],
                    "reviewed_operations": [
                        {"source_ref": row["source_ref"],
                         "function_ordinal": row["function_ordinal"],
                         "classification": row["classification"].replace("_", " "),
                         "description": row["description"],
                         "limits": row["limits"]}
                        for row in study["reviewed_client_operations"]
                    ],
                    "open_static_questions": study["open_static_questions"],
                }
            static_ast_path = ROOT / (base + "/chat_ast_followup.json")
            if static_ast_path.is_file():
                ast_study = read(base + "/chat_ast_followup.json")
                if ast_study["specimen_id"] != item["id"] or ast_study["version"] != number:
                    raise ValueError("Chat AST follow-up identity mismatch")
                visuals["chat_ast_followup"] = {
                    "status": ast_study["review_status"],
                    "source_scope": ast_study["source_scope"],
                    "verified_live_behavior": ast_study["live_behavior_verified"],
                    "parsed_bundles": ast_study["ast_census"]["parsed_javascript_bundles"],
                    "candidate_functions": ast_study["structural_candidates"]["candidate_function_nodes"],
                    "candidate_bundles": ast_study["structural_candidates"]["source_bundles_with_candidate_functions"],
                    "cooccurrences": [
                        {"label": key.replace("_and_", " + ").replace("_", " "),
                         "count": count}
                        for key, count in ast_study["member_property_cooccurrence_functions"].items()
                    ],
                    "member_writes": [
                        {"label": name, "count": count}
                        for name, count in ast_study["member_property_assignment_functions"].items()
                    ],
                    "unresolved": ast_study["unresolved"],
                    "limitations": ast_study["limitations"],
                }
            export_format_path = ROOT / (base + "/export_format_research.json")
            if export_format_path.is_file():
                research = read(base + "/export_format_research.json")
                if research["specimen_id"] != item["id"] or research["version"] != number:
                    raise ValueError("Export research identity mismatch")
                visuals["chat_export_format"] = {
                    "evidence_ref": "E2-070",
                    "scope": "public_reference",
                    "fields": [{
                        "field": f["field"], "meaning": f["meaning"]
                    } for f in research["export_tree_fields"]],
                    "operations": research["derived_operations"],
                    "sources": [{
                        "title": research["official"]["source_title"],
                        "url": research["official"]["source_url"],
                        "authority": "official"
                    }] + [{
                        "title": s["source_title"], "url": s["source_url"],
                        "authority": "community"
                    } for s in research["community"]],
                    "limitations": research["limitations"]
                }
            public_actions_path = ROOT / (base + "/public_chat_actions.json")
            if public_actions_path.is_file():
                documented = read(base + "/public_chat_actions.json")
                if documented["specimen_id"] != item["id"] or documented["version"] != number:
                    raise ValueError("Public chat action inventory identity mismatch")
                visuals["public_chat_actions"] = {
                    "scope": "official_public_documentation",
                    "actions": [{
                        "id": action["id"], "name": action["name"],
                        "status": action["status"],
                        "summary": action["summary"],
                        "documented_date": action["documented_date"],
                        "source_title": action["source_title"],
                        "source_url": action["source_url"],
                        "graph_events": action["graph_events"],
                        "capture_ref": action["capture_ref"],
                        "unknown": action["unknown"]
                    } for action in documented["actions"]]
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
                    protocol_path = ROOT / "queues/chat_runtime_protocols.json"
                    if protocol_path.is_file():
                        protocols = read("queues/chat_runtime_protocols.json")
                        if protocols["format_version"] != 1 or protocols["feature_id"] != "chat-interaction":
                            raise ValueError("Chat runtime protocol identity mismatch")
                        open_ids = {task["id"] for task in research["tasks"]
                                    if task["status"] == "requires_new_evidence"}
                        planned_ids = [entry["task_id"] for entry in protocols["protocols"]]
                        if set(planned_ids) != open_ids or len(planned_ids) != len(open_ids):
                            raise ValueError("Chat protocols must match open runtime tasks")
                        visuals["feature_research"]["protocols"] = [
                            {"task_id": entry["task_id"], "question": entry["question"],
                             "discriminators": entry["discriminators"],
                             "observables": entry["observables"],
                             "stop_condition": entry["stop_condition"],
                             "evidence_status": entry["evidence_status"]}
                            for entry in protocols["protocols"]
                        ]
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
