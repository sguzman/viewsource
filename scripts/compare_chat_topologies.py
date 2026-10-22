"""Compare *normalized* export trees by anonymous structural equivalence.

This module never touches the network or source exports. It accepts the
ordinal-only output of normalize_conversation(), refuses inconsistent graphs,
and does not return or persist any stable graph signature, IDs, or node lists.
Structural equivalence cannot establish common message identity or causation.
"""
from __future__ import annotations

from collections import deque


class TopologyError(ValueError):
    """Invalid normalized graph; errors deliberately omit source identifiers."""


def _read_topology(graph: dict) -> dict:
    if not isinstance(graph, dict) or graph.get("source") != "local_export_tree":
        raise TopologyError("Expected a normalized local export graph")
    if graph.get("format_version") != 1 or graph.get("live_implementation_verified") is not False:
        raise TopologyError("Unsupported export graph version or evidence status")
    nodes = graph.get("nodes")
    if not isinstance(nodes, list):
        raise TopologyError("Invalid node collection")
    if type(graph.get("node_count")) is not int or graph["node_count"] != len(nodes):
        raise TopologyError("Node count disagrees with graph")
    parents: dict[str, str | None] = {}
    actors: dict[str, str] = {}
    for node in nodes:
        if not isinstance(node, dict):
            raise TopologyError("Invalid node record")
        key, parent, actor = node.get("ordinal"), node.get("parent"), node.get("actor")
        if not isinstance(key, str) or not key or key in parents:
            raise TopologyError("Invalid or repeated ordinal")
        if parent is not None and (not isinstance(parent, str) or not parent):
            raise TopologyError("Invalid parent reference")
        if actor not in ("user", "assistant", "other"):
            raise TopologyError("Unsupported actor category")
        parents[key] = parent
        actors[key] = actor

    children: dict[str, list[str]] = {key: [] for key in parents}
    roots: list[str] = []
    for key, parent in parents.items():
        if parent is None:
            roots.append(key)
        elif parent not in children:
            raise TopologyError("Dangling parent")
        else:
            children[parent].append(key)

    order: list[str] = []
    depths: dict[str, int] = {}
    queue = deque(roots)
    for root in roots:
        depths[root] = 0
    while queue:
        key = queue.popleft()
        order.append(key)
        for child in children[key]:
            depths[child] = depths[key] + 1
            queue.append(child)
    if len(order) != len(nodes):
        raise TopologyError("Cyclic or disconnected topology")

    path = graph.get("selected_path")
    status = graph.get("selected_path_status")
    if not isinstance(path, list) or status not in ("missing", "resolved"):
        raise TopologyError("Unsupported selection state")
    if (status == "resolved") != bool(path):
        raise TopologyError("Selection status disagrees with path")
    for i, key in enumerate(path):
        if not isinstance(key, str) or key not in parents:
            raise TopologyError("Invalid selected node")
        if parents[key] != (path[i - 1] if i else None):
            raise TopologyError("Selected path does not follow ancestry")

    branch_points = sum(len(items) >= 2 for items in children.values())
    alternatives = sum(max(0, len(items) - 1) for items in children.values())
    for field, expected in (("branch_point_count", branch_points),
                            ("alternative_child_count", alternatives)):
        if type(graph.get(field)) is not int or graph[field] != expected:
            raise TopologyError("Branch counts disagree with graph")
    counts = {
        "nodes": len(nodes),
        "roots": len(roots),
        "parent_edges": len(nodes) - len(roots),
        "branch_points": branch_points,
        "alternative_children": alternatives,
        "max_depth": max(depths.values(), default=0),
        "selected_path_length": len(path),
        "user_nodes": sum(role == "user" for role in actors.values()),
        "assistant_nodes": sum(role == "assistant" for role in actors.values()),
        "other_nodes": sum(role == "other" for role in actors.values()),
    }
    return dict(children=children, roots=roots, order=order,
                actors=actors, selected=set(path), counts=counts)


def _forest_equivalence(left: dict, right: dict, *, mark_selection: bool) -> bool:
    # Intern equivalent subtrees into identical ephemeral integers *within
    # this comparison only*. No signatures leave the function or get logged.
    intern: dict[tuple, int] = {}

    def encode(graph: dict) -> tuple[int, ...]:
        signatures: dict[str, int] = {}
        for key in reversed(graph["order"]):
            signature = (
                graph["actors"][key],
                key in graph["selected"] if mark_selection else False,
                tuple(sorted(signatures[child] for child in graph["children"][key])),
            )
            if signature not in intern:
                intern[signature] = len(intern) + 1
            signatures[key] = intern[signature]
        return tuple(sorted(signatures[root] for root in graph["roots"]))

    return encode(left) == encode(right)


def compare_normalized_trees(before: dict, after: dict) -> dict:
    """Compare anonymized trees without correlating original or ordinal IDs.

    Equal selection shape does NOT prove the same branch was selected; sibling
    subtrees with the same actors and structure can be indistinguishable.
    Differences do NOT identify which UI action caused them.
    """
    a, b = _read_topology(before), _read_topology(after)
    metrics_a, metrics_b = a["counts"], b["counts"]
    return {
        "format_version": 1,
        "scope": "local_anonymous_export_structure",
        "unmarked_structure_equivalent": _forest_equivalence(a, b, mark_selection=False),
        "selection_marked_structure_equivalent": _forest_equivalence(a, b, mark_selection=True),
        "metric_deltas": {field: metrics_b[field] - metrics_a[field]
                          for field in metrics_a},
        "message_identity_correlated": False,
        "live_behavior_verified": False,
        "limitations": [
            "No original IDs, titles, content, or durable fingerprints are returned.",
            "Isomorphic siblings can conceal a selected-branch change.",
            "Structural changes cannot be attributed to edits, retries, or branching actions.",
            "Export shape equivalence does not establish live storage or API semantics.",
        ],
    }
