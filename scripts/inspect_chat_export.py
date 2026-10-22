#!/usr/bin/env python3
"""Local-only structural inspection of ChatGPT JSON export trees.

No captured records, user IDs, titles, messages, routes or filenames are
included in output. This tool is not called by the public website builder.
It analyzes documented legacy export-style mapping trees, NOT the live API.
Uses incremental JSON-array parsing; huge individual records can still consume memory.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


class ExportShapeError(ValueError):
    """The input is not a supported local export container."""


def _reject_duplicate_keys(pairs):
    """Fail closed on duplicate JSON fields, including nested message objects.

    No offending field name or content is reflected into the exception.
    """
    fields = {}
    for name, value in pairs:
        if name in fields:
            raise ExportShapeError("Duplicate JSON object key")
        fields[name] = value
    return fields


def _reject_nonfinite(_value):
    """Reject nonstandard NaN/Infinity literals without printing source data."""
    raise ExportShapeError("Non-finite JSON number")


def inspect_conversation(value: object) -> dict:
    """Return aggregate counts only, without any original keys or content."""
    result = {
        "shape": "unsupported",
        "flat_message_items": 0,
        "nodes": 0,
        "message_nodes": 0,
        "null_message_nodes": 0,
        "parent_links": 0,
        "branch_points": 0,
        "alternative_children": 0,
        "duplicate_child_links": 0,
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
            # The array is only an ordered collection. There is no
            # supported parent/alternative graph to reconstruct from it.
            result["flat_message_items"] = len(value["messages"])
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
        # Only distinct, string-valued links count as possible alternatives.
        # Duplicates are invalid links, not extra replies.
        unique_children = {child for child in child_list if isinstance(child, str)}
        result["duplicate_child_links"] += sum(
            isinstance(child, str) for child in child_list
        ) - len(unique_children)
        result["branch_points"] += int(len(unique_children) >= 2)
        result["alternative_children"] += max(0, len(unique_children) - 1)
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


def summarize_records(records) -> dict:
    """Accumulate counts without retaining parsed conversation records."""
    total = 0
    fields = (
        "flat_message_items", "nodes", "message_nodes",
        "null_message_nodes", "parent_links",
        "branch_points", "alternative_children", "duplicate_child_links",
        "roots",
        "dangling_parent_links", "dangling_child_links",
        "parent_child_conflicts", "ancestry_cycles",
    )
    counts = {key: 0 for key in fields}
    shapes = {"mapping_tree": 0, "flat_messages_no_tree": 0, "unsupported": 0}
    selection = {status: 0 for status in
                 ("resolved", "missing", "dangling", "cycle", "unresolved", "not_available")}
    selected_length_total = 0
    off_path_total = 0
    for conversation in records:
        total += 1
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
        "conversation_count": total,
        "shapes": shapes,
        "selection_status": selection,
        "structural_counts": counts,
        "resolved_selected_path_nodes_total": selected_length_total,
        "resolved_off_path_nodes_total": off_path_total,
        "limits": [
            "No message text or identifiers are returned.",
            "Counts cannot identify live ChatGPT route or backend semantics.",
            "Flat message-array lengths are counted separately; no ancestry or branch identity is inferred.",
            "This is a local-only export snapshot; format variants may be unsupported.",
        ],
    }


def inspect_export(data: object) -> dict:
    """Compatibility entrypoint for in-memory synthetic tests."""
    if not isinstance(data, list):
        raise ExportShapeError("Expected a list of conversation records")
    return summarize_records(iter(data))


def iter_export_records(stream, *, chunk_size: int = 65536):
    """Yield top-level JSON array records with one lexical scan per character.

    Only one record is buffered at a time, up to the configured record limit.
    A string-aware depth scanner finds top-level delimiters, then JSONDecoder
    validates each *complete* record once (including duplicate-key checks).
    This avoids reparsing the entire growing record at every chunk boundary.
    """
    if type(chunk_size) is not int or not (1 <= chunk_size <= 1024 * 1024):
        raise ExportShapeError("Chunk size must be a bounded positive integer")
    decoder = json.JSONDecoder(
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_nonfinite,
    )
    state = "start"
    nesting = 0
    in_string = False
    escaped = False
    fragments: list[str] = []
    record_chars = 0
    max_record_chars = 128 * 1024 * 1024

    def keep(fragment: str) -> None:
        nonlocal record_chars
        if fragment:
            record_chars += len(fragment)
            if record_chars > max_record_chars:
                raise ExportShapeError("Oversized export record")
            fragments.append(fragment)

    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        # A partially read value resumes from the start of this chunk.
        segment_start = 0 if state == "record" else None
        for index, char in enumerate(chunk):
            if state == "done":
                if not char.isspace():
                    raise ExportShapeError("Trailing characters after array")
                continue
            if state == "start":
                if char.isspace():
                    continue
                if char != "[":
                    raise ExportShapeError("Expected JSON export array")
                state = "first_or_end"
                continue
            if state in ("first_or_end", "value"):
                if char.isspace():
                    continue
                if char == "]":
                    if state == "value":
                        raise ExportShapeError("Trailing comma")
                    state = "done"
                    continue
                state = "record"
                segment_start = index

            if state == "record":
                if not in_string and nesting == 0 and char in ",]":
                    # The outer array delimiter is not part of the record.
                    keep(chunk[segment_start:index])
                    # Full JSON validation is performed exactly once per
                    # completed record, not once per incoming chunk.
                    yield decoder.decode("".join(fragments))
                    fragments.clear()
                    record_chars = 0
                    nesting = 0
                    in_string = False
                    escaped = False
                    segment_start = None
                    state = "value" if char == "," else "done"
                    continue
                if in_string:
                    if escaped:
                        escaped = False
                    elif char == "\\":
                        escaped = True
                    elif char == '"':
                        in_string = False
                elif char == '"':
                    in_string = True
                elif char in "[{":
                    nesting += 1
                elif char in "]}":
                    nesting -= 1
                    if nesting < 0:
                        raise ExportShapeError("Invalid nested structure")
                continue

            raise ExportShapeError("Invalid export array separator")
        if state == "record":
            keep(chunk[segment_start:])
    if state != "done":
        raise ExportShapeError("Truncated export array")


def inspect_file(path: Path) -> dict:
    """Read one record at a time and return only aggregate counts."""
    with path.open("r", encoding="utf-8") as source:
        return summarize_records(iter_export_records(source))


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect only the structure of a local ChatGPT export")
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        # This file can contain sensitive user information: never copy it
        # into Git, stdout, diagnostic logs or a public specimen record.
        summary = inspect_file(args.input)
    except (OSError, ValueError, TypeError, MemoryError, RecursionError):
        parser.exit(2, "Local export inspection failed (input/path details suppressed)\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
