#!/usr/bin/env python3
"""Local-only structural inspection of ChatGPT JSON export trees.

No captured records, user IDs, titles, messages, routes or filenames are
included in output. This tool is not called by the public website builder.
It analyzes documented legacy export-style mapping trees, NOT the live API.
Uses Python's in-memory JSON parser; process one export shard at a time.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


class ExportShapeError(ValueError):
    """The input is not a supported local export container."""


def inspect_conversation(value: object) -> dict:
    """Return aggregate counts only, without any original keys or content."""
    result = {
        "shape": "unsupported",
        "nodes": 0,
        "message_nodes": 0,
        "null_message_nodes": 0,
        "parent_links": 0,
        "branch_points": 0,
        "alternative_children": 0,
        "roots": 0,
        "dangling_parent_links": 0,
        "dangling_child_links": 0,
        "parent_child_conflicts": 0,
        "ancestry_cycles": 0,
        "selected_path_length": None,
        "off_path_nodes": None,
        "selected_path_status": "not_available",
    }
    if not isinstance(value, dict):
        return result
    mapping = value.get("mapping")
    if not isinstance(mapping, dict):
        if isinstance(value.get("messages"), list):
            result["shape"] = "flat_messages_no_tree"
        return result
    result["shape"] = "mapping_tree"
    result["nodes"] = len(mapping)
    children = {}
    parents = {}
    for key, node in mapping.items():
        if not isinstance(node, dict):
            result["parent_child_conflicts"] += 1
            continue
        has_message = node.get("message") is not None
        result["message_nodes" if has_message else "null_message_nodes"] += 1
        parent = node.get("parent")
        parents[key] = parent
        if parent is None:
            result["roots"] += 1
        elif isinstance(parent, str):
            result["parent_links"] += 1
            if parent not in mapping:
                result["dangling_parent_links"] += 1
        else:
            result["parent_child_conflicts"] += 1
        child_list = node.get("children", [])
        if not isinstance(child_list, list):
            result["parent_child_conflicts"] += 1
            child_list = []
        children[key] = child_list
        result["branch_points"] += int(len(child_list) >= 2)
        result["alternative_children"] += max(0, len(child_list) - 1)
    for key, child_list in children.items():
        for child in child_list:
            if not isinstance(child, str) or child not in mapping:
                result["dangling_child_links"] += 1
            elif parents.get(child) != key:
                result["parent_child_conflicts"] += 1
        parent = parents.get(key)
        if isinstance(parent, str) and parent in mapping:
            if key not in children.get(parent, []):
                result["parent_child_conflicts"] += 1

    # Parent-chain cycle detection across the whole tree. Never log keys.
    visited = set()
    for key in mapping:
        if key in visited:
            continue
        here = key
        trace = set()
        while here in mapping and here not in visited and here not in trace:
            trace.add(here)
            here = parents.get(here)
        if here in trace:
            result["ancestry_cycles"] += 1
        visited.update(trace)

    current = value.get("current_node")
    if not isinstance(current, str) or not current:
        result["selected_path_status"] = "missing"
    elif current not in mapping:
        result["selected_path_status"] = "dangling"
    else:
        here = current
        seen = set()
        while isinstance(here, str) and here in mapping and here not in seen:
            seen.add(here)
            here = parents.get(here)
        if here in seen:
            result["selected_path_status"] = "cycle"
        elif here is not None:
            result["selected_path_status"] = "unresolved"
        else:
            result["selected_path_status"] = "resolved"
            result["selected_path_length"] = len(seen)
            result["off_path_nodes"] = len(mapping) - len(seen)
    return result


def inspect_export(data: object) -> dict:
    """Summarize one export shard; never expose record-level identifiers."""
    if not isinstance(data, list):
        raise ExportShapeError("Expected a list of conversation records")
    fields = (
        "nodes", "message_nodes", "null_message_nodes", "parent_links",
        "branch_points", "alternative_children", "roots",
        "dangling_parent_links", "dangling_child_links",
        "parent_child_conflicts", "ancestry_cycles",
    )
    counts = {key: 0 for key in fields}
    shapes = {"mapping_tree": 0, "flat_messages_no_tree": 0, "unsupported": 0}
    selection = {status: 0 for status in
                 ("resolved", "missing", "dangling", "cycle", "unresolved", "not_available")}
    selected_length_total = 0
    off_path_total = 0
    for conversation in data:
        item = inspect_conversation(conversation)
        shapes[item["shape"]] += 1
        selection[item["selected_path_status"]] += 1
        for key in fields:
            counts[key] += item[key]
        if item["selected_path_status"] == "resolved":
            selected_length_total += item["selected_path_length"]
            off_path_total += item["off_path_nodes"]
    return {
        "format_version": 1,
        "source": "local_export_structure",
        "external_format_evidence_only": True,
        "live_chat_implementation_verified": False,
        "conversation_count": len(data),
        "shapes": shapes,
        "selection_status": selection,
        "structural_counts": counts,
        "resolved_selected_path_nodes_total": selected_length_total,
        "resolved_off_path_nodes_total": off_path_total,
        "limits": [
            "No message text or identifiers are returned.",
            "Counts cannot identify live ChatGPT route or backend semantics.",
            "Flat messages arrays do not establish branching and are not guessed into trees.",
            "This is a local-only export snapshot; format variants may be unsupported.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect only the structure of a local ChatGPT export")
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        # This file can contain sensitive user information: never copy it
        # into Git, stdout, diagnostic logs or a public specimen record.
        data = json.loads(args.input.read_text(encoding="utf-8"))
        summary = inspect_export(data)
    except (OSError, ValueError, TypeError, MemoryError):
        parser.exit(2, "Local export inspection failed (input/path details suppressed)\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
