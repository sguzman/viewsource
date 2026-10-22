#!/usr/bin/env python3
"""Standard-library checks for evidence-bounded technology and feature graphs."""
from __future__ import annotations
from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def validate_extensions(require, specimen_id: str, version: int) -> None:
    base = f"specimens/{specimen_id}/v{version:04d}"
    tech_path = ROOT / base / "technology_inventory.json"
    graph_path = ROOT / base / "chat-interaction.graph.json"
    if not tech_path.exists() and not graph_path.exists():
        return
    record = read(base + "/record.json")
    components = {c["id"]: c for c in record["components"]}
    evidence = {f["evidence"].get("evidence_ref") for f in record["findings"]}
    if tech_path.exists():
        inventory = read(base + "/technology_inventory.json")
        require(inventory.get("format_version") == 1 and inventory.get("specimen_id") == specimen_id
                and inventory.get("version") == version, "Technology inventory identity")
        ids = [x["id"] for x in inventory["technologies"]]
        require(len(ids) == len(set(ids)), "Repeated technology IDs")
        for t in inventory["technologies"]:
            ref = t.get("component_ref")
            require(ref in components and components.get(ref, {}).get("kind") == "Dependency",
                    f"Technology component link missing: {t['id']}")
            require(t["confidence"] in {"strong", "likely", "indicator"},
                    f"Technology confidence: {t['id']}")
            require(t.get("version") is None or isinstance(t.get("version"), str),
                    f"Technology version type: {t['id']}")
            require(len(t["observations"]) > 0 and all(
                isinstance(m.get("matches"), int) and m["matches"] >= m["files"] > 0
                for m in t["observations"]), f"Invalid technology evidence counts: {t['id']}")
    if not graph_path.exists():
        return
    require(tech_path.exists(), "Feature graph must have a technology inventory")
    graph = read(base + "/chat-interaction.graph.json")
    require(graph.get("format_version") == 1 and graph.get("specimen_id") == specimen_id
            and graph.get("version") == version and graph.get("source_scope") == record["capture_scope"],
            "Feature graph identity or capture scope mismatch")
    require(graph.get("model_status") in {"candidate", "partially_verified", "verified"},
            "Invalid feature-graph status")
    machine_ids = [m["id"] for m in graph["machines"]]
    event_ids = [e["id"] for e in graph["events"]]
    states = {}
    require(len(machine_ids) == len(set(machine_ids)), "Duplicate machine IDs")
    require(len(event_ids) == len(set(event_ids)), "Duplicate event IDs")
    for machine in graph["machines"]:
        ids = [s["id"] for s in machine["states"]]
        require(len(ids) == len(set(ids)) and machine["initial_state"] in ids,
                f"Invalid initial state or repeated state in {machine['id']}")
        states[machine["id"]] = set(ids)
    for surface in graph["surfaces"]:
        ref = surface["component_ref"]
        require(ref in components and components[ref]["kind"] in {"DOMRegion", "Form", "Page"},
                f"Bad surface ontology reference: {ref}")
        require(surface["basis"] in {"observed_static", "observed_live", "hypothesis"},
                f"Invalid surface evidence basis: {ref}")
        require(set(surface["evidence_refs"]) <= evidence, f"Unknown surface evidence: {ref}")
        if surface["basis"] == "hypothesis":
            require(not surface["evidence_refs"], f"Unsupported speculative UI evidence: {ref}")
        else:
            require(bool(surface["evidence_refs"]), f"Missing observed UI evidence: {ref}")
    for link in graph["technology_links"]:
        ref = link["component_ref"]
        require(ref in components and components[ref]["kind"] == "Dependency",
                f"Unlinked feature library: {ref}")
        require(set(link["evidence_refs"]) <= evidence, f"Unknown technology evidence: {ref}")
        require(link["evidence_status"] in {"static_presence", "verified_feature_use", "hypothesis"},
                f"Invalid library status: {ref}")
        if link["evidence_status"] != "verified_feature_use":
            require(link["feature_ownership_verified"] is False,
                    f"Library source presence cannot claim feature ownership: {ref}")
    ids = [t["id"] for t in graph["transitions"]]
    require(len(ids) == len(set(ids)), "Repeated transition IDs")
    for t in graph["transitions"]:
        machine = t["machine"]
        require(machine in states, f"Transition references unknown machine: {t['id']}")
        require(t["from"] in states.get(machine, set()) and t["to"] in states.get(machine, set()),
                f"Dangling state transition: {t['id']}")
        require(t["event"] in event_ids, f"Unknown event: {t['id']}")
        require(t["evidence_status"] in {"hypothesis", "observed_live"},
                f"Invalid transition evidence: {t['id']}")
        require(bool(t["verify"]), f"Missing verification instructions: {t['id']}")
        require(set(t["evidence_refs"]) <= evidence, f"Unknown transition refs: {t['id']}")
        if t["evidence_status"] == "hypothesis":
            require(not t["evidence_refs"], f"Hypothetical edge cannot claim evidence: {t['id']}")
        else:
            require(bool(t["evidence_refs"]), f"Verified edge requires evidence: {t['id']}")
            require(graph["source_scope"] == "live_test",
                    f"Static-only graph cannot assert observed live interaction: {t['id']}")
    for group in ("surfaces", "entities", "events", "open_questions"):
        names = [node["id"] for node in graph[group]]
        require(len(names) == len(set(names)), f"Duplicate feature nodes in {group}")
    if graph["source_scope"] != "live_test":
        require(all(t["evidence_status"] == "hypothesis" for t in graph["transitions"]),
                "Saved capture contains no verified live state transitions")
