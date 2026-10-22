"""Normalize a local export tree into a content-free ordinal message graph.

This module has NO command-line output or access to a browser or network.
Only caller-authorized code should load local exports. No raw records,
message content, conversation IDs, route values or source node IDs are saved.
This describes an export snapshot, not the site's live implementation.
"""
from __future__ import annotations

from collections import deque

from inspect_chat_export import inspect_conversation


class ExportGraphError(ValueError):
    """The export structure cannot be normalized without guessing."""


def normalize_conversation(conversation: dict) -> dict:
    """Produce ordinal-only parent links and the selected ancestry path."""
    metrics = inspect_conversation(conversation)
    if metrics["shape"] != "mapping_tree":
        raise ExportGraphError("A tree mapping is required")
    for key in ("dangling_parent_links", "dangling_child_links",
                "parent_child_conflicts", "ancestry_cycles"):
        if metrics[key]:
            raise ExportGraphError("Cannot normalize an inconsistent tree")
    if metrics["selected_path_status"] not in ("resolved", "missing"):
        raise ExportGraphError("Selected node does not resolve")

    mapping = conversation["mapping"]
    by_parent: dict[str, list[str]] = {}
    roots: list[str] = []
    for key, node in mapping.items():
        if not isinstance(key, str) or not isinstance(node, dict):
            raise ExportGraphError("Unsupported node shape")
        parent = node.get("parent")
        if parent is None:
            roots.append(key)
        else:
            by_parent.setdefault(parent, []).append(key)
    pending = deque(roots)
    visited: set[str] = set()
    ordering: list[str] = []
    while pending:
        key = pending.popleft()
        if key in visited:
            raise ExportGraphError("Repeated node traversal")
        visited.add(key)
        ordering.append(key)
        pending.extend(by_parent.get(key, ()))
    if len(ordering) != len(mapping):
        raise ExportGraphError("Disconnected or cyclic ancestry")
    ordinals = {key: "n" + str(i).zfill(4)
                for i, key in enumerate(ordering, start=1)}
    nodes = []
    for key in ordering:
        item = mapping[key]
        message = item.get("message")
        author = message.get("author") if isinstance(message, dict) else None
        role = author.get("role") if isinstance(author, dict) else None
        nodes.append({
            "ordinal": ordinals[key],
            "parent": ordinals.get(item.get("parent")),
            "actor": role if role in ("user", "assistant") else "other",
        })
    selected = []
    if metrics["selected_path_status"] == "resolved":
        key = conversation["current_node"]
        while key is not None:
            selected.append(ordinals[key])
            key = mapping[key].get("parent")
        selected.reverse()
    return {
        "format_version": 1,
        "source": "local_export_tree",
        "live_implementation_verified": False,
        "node_count": len(nodes),
        "nodes": nodes,
        "selected_path": selected,
        "selected_path_status": metrics["selected_path_status"],
        "branch_point_count": metrics["branch_points"],
        "alternative_child_count": metrics["alternative_children"],
        "limits": [
            "Ordinals are temporary and not stable across independent exports.",
            "Only actor categories and structural links are represented.",
            "No cross-conversation ancestry can be inferred from one export tree.",
            "Export structure is not proof of the live website's internal model.",
        ],
    }
