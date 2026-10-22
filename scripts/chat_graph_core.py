"""Synthetic, content-free ancestry model for Viewsource feature research.

NOT the verified ChatGPT message schema. Keys must be invented local test IDs.
No network, persistence, account IDs, message text, or browser integration.
"""
from __future__ import annotations

from dataclasses import dataclass


class GraphError(ValueError):
    """An invalid operation on a candidate chat graph."""


@dataclass(frozen=True)
class MessageNode:
    local_key: str
    parent_key: str | None
    actor: str


@dataclass(frozen=True)
class ConversationFork:
    source_chat_key: str
    source_message_key: str
    destination_chat_key: str


class ConversationGraph:
    """Immutable parent links and one optionally selected leaf."""

    def __init__(self, local_chat_key: str) -> None:
        if not local_chat_key:
            raise GraphError("A synthetic chat key is required")
        self.local_chat_key = local_chat_key
        self._nodes: dict[str, MessageNode] = {}
        self.selected_leaf: str | None = None

    @property
    def nodes(self) -> tuple[MessageNode, ...]:
        return tuple(self._nodes.values())

    def add(self, local_key: str, parent_key: str | None, actor: str) -> MessageNode:
        if not local_key or local_key in self._nodes:
            raise GraphError("Node key must be nonempty and unique")
        if actor not in {"user", "assistant", "other"}:
            raise GraphError("Unknown actor category")
        if parent_key is not None and parent_key not in self._nodes:
            raise GraphError("Parent must exist before child insertion")
        node = MessageNode(local_key, parent_key, actor)
        self._nodes[local_key] = node
        # Appending a child invalidates leaf selection. Do not guess whether
        # the website would automatically follow the newly created child.
        if parent_key == self.selected_leaf:
            self.selected_leaf = None
        return node

    def _get(self, key: str) -> MessageNode:
        if key not in self._nodes:
            raise GraphError("Unknown local node key")
        return self._nodes[key]

    def lineage(self, key: str) -> tuple[MessageNode, ...]:
        path: list[MessageNode] = []
        seen: set[str] = set()
        current: str | None = key
        while current is not None:
            if current in seen:
                raise GraphError("Ancestry cycle found")
            seen.add(current)
            node = self._get(current)
            path.append(node)
            current = node.parent_key
        return tuple(reversed(path))

    def children(self, key: str) -> tuple[MessageNode, ...]:
        self._get(key)
        return tuple(node for node in self.nodes if node.parent_key == key)

    def siblings(self, key: str) -> tuple[MessageNode, ...]:
        node = self._get(key)
        return tuple(candidate for candidate in self.nodes
                     if candidate.parent_key == node.parent_key and candidate.local_key != key)

    def select(self, key: str | None) -> tuple[str, ...]:
        if key is None:
            self.selected_leaf = None
            return ()
        path = self.lineage(key)
        if self.children(key):
            raise GraphError("Selection must reference a leaf")
        self.selected_leaf = key
        return tuple(node.local_key for node in path)

    def local_structure(self) -> dict:
        """Returned keys are caller-supplied; callers must use synthetic IDs."""
        return {
            "chat": self.local_chat_key,
            "nodes": [{"key": node.local_key, "parent": node.parent_key, "actor": node.actor}
                      for node in self.nodes],
            "selected_path": list(self.select(self.selected_leaf)) if self.selected_leaf else [],
        }

    def topology_metrics(self) -> dict[str, int]:
        """Count structural features without exposing local node identity.

        This measures the synthetic model only; it cannot identify which real
        chat action, if any, caused a change in an observed interface.
        """
        children: dict[str, int] = {}
        depth: dict[str, int] = {}
        nodes = self.nodes
        for node in nodes:
            if node.parent_key is None:
                depth[node.local_key] = 0
            else:
                children[node.parent_key] = children.get(node.parent_key, 0) + 1
                depth[node.local_key] = depth[node.parent_key] + 1
        return {
            "node_count": len(nodes),
            "root_count": sum(node.parent_key is None for node in nodes),
            "parent_edge_count": sum(node.parent_key is not None for node in nodes),
            "branch_point_count": sum(count >= 2 for count in children.values()),
            "alternative_child_count": sum(max(count - 1, 0) for count in children.values()),
            "max_depth": max(depth.values(), default=0),
            "selected_path_length": (depth[self.selected_leaf] + 1)
            if self.selected_leaf is not None else 0,
        }

    def anonymous_topology(self) -> dict:
        """Return topology only; NEVER include caller-supplied node/chat keys.

        Ordinals follow insertion order. They provide structural comparison
        within one export, not stable site identities or cross-run correlation.
        """
        names = {node.local_key: f"n{i:04d}"
                 for i, node in enumerate(self.nodes, start=1)}
        path = self.lineage(self.selected_leaf) if self.selected_leaf else ()
        return {
            "node_count": len(names),
            "nodes": [
                {"ordinal": names[node.local_key],
                 "parent": names[node.parent_key] if node.parent_key else None,
                 "actor": node.actor}
                for node in self.nodes
            ],
            "selected_path": [names[node.local_key] for node in path],
        }


class ConversationForest:
    """Independent conversation graphs plus possible cross-chat fork links.

    A candidate fork is not evidence that the actual site clones, references
    or copies message nodes when starting another conversation.
    """

    def __init__(self) -> None:
        self.chats: dict[str, ConversationGraph] = {}
        self.forks: list[ConversationFork] = []

    def new_chat(self, key: str) -> ConversationGraph:
        if not key or key in self.chats:
            raise GraphError("Conversation keys must be nonempty and unique")
        chat = ConversationGraph(key)
        self.chats[key] = chat
        return chat

    def annotate_candidate_fork(self, source_chat: str, source_message: str,
                                destination_chat: str) -> ConversationFork:
        if source_chat not in self.chats or destination_chat not in self.chats:
            raise GraphError("Both chat roots must exist")
        if source_chat == destination_chat:
            raise GraphError("Cross-chat forks need distinct chat roots")
        self.chats[source_chat].lineage(source_message)
        # A cross-conversation ancestry model must remain acyclic.
        # Existing directed edges are source -> destination.
        reachable = {destination_chat}
        frontier = [destination_chat]
        while frontier:
            node = frontier.pop()
            for existing in self.forks:
                if existing.source_chat_key == node and existing.destination_chat_key not in reachable:
                    reachable.add(existing.destination_chat_key)
                    frontier.append(existing.destination_chat_key)
        if source_chat in reachable:
            raise GraphError("Candidate fork would create a conversation cycle")
        fork = ConversationFork(source_chat, source_message, destination_chat)
        if fork in self.forks:
            raise GraphError("Duplicate candidate fork")
        self.forks.append(fork)
        return fork

    def topology_metrics(self) -> dict[str, int]:
        """Aggregate only counts; no opaque keys or stable fingerprints."""
        per_chat = [chat.topology_metrics() for chat in self.chats.values()]
        return {
            "conversation_count": len(self.chats),
            "node_count": sum(m["node_count"] for m in per_chat),
            "parent_edge_count": sum(m["parent_edge_count"] for m in per_chat),
            "branch_point_count": sum(m["branch_point_count"] for m in per_chat),
            "alternative_child_count": sum(m["alternative_child_count"] for m in per_chat),
            "candidate_fork_count": len(self.forks),
            "selected_conversation_count": sum(m["selected_path_length"] > 0 for m in per_chat),
        }

    def anonymous_topology(self) -> dict:
        """Return anonymized per-conversation trees and hypothetical fork edges.

        Local keys never leave this projection. Fork and node ordinals are
        temporary presentation positions, not real product identifiers.
        """
        chat_ordinals = {key: f"c{i:04d}"
                         for i, key in enumerate(self.chats, start=1)}
        node_ordinals = {
            key: {node.local_key: f"n{i:04d}"
                  for i, node in enumerate(chat.nodes, start=1)}
            for key, chat in self.chats.items()
        }
        return {
            "conversation_count": len(self.chats),
            "chats": [
                {"ordinal": chat_ordinals[key],
                 **chat.anonymous_topology()}
                for key, chat in self.chats.items()
            ],
            "candidate_forks": [
                {"source_chat": chat_ordinals[edge.source_chat_key],
                 "source_node": node_ordinals[edge.source_chat_key][edge.source_message_key],
                 "destination_chat": chat_ordinals[edge.destination_chat_key]}
                for edge in self.forks
            ]
        }


CHAT_STRUCTURE_KEYS = frozenset((
    "node_count", "root_count", "parent_edge_count", "branch_point_count",
    "alternative_child_count", "max_depth", "selected_path_length"
))
FOREST_STRUCTURE_KEYS = frozenset((
    "conversation_count", "node_count", "parent_edge_count",
    "branch_point_count", "alternative_child_count",
    "candidate_fork_count", "selected_conversation_count"
))


def compare_topology_metrics(before: dict, after: dict) -> dict:
    """Return structural deltas, never object identities or semantic claims.

    Matching counts are NOT proof that message graphs are the same, and a
    count change alone cannot distinguish editing, regeneration or branching.
    """
    if not isinstance(before, dict) or not isinstance(after, dict):
        raise GraphError("Metrics must be maps")
    fields = frozenset(before)
    if fields != frozenset(after) or fields not in (
            CHAT_STRUCTURE_KEYS, FOREST_STRUCTURE_KEYS):
        raise GraphError("Only supported structural metrics can be compared")
    if any(type(before[key]) is not int or type(after[key]) is not int
           or before[key] < 0 or after[key] < 0 for key in fields):
        raise GraphError("All structural counts must be nonnegative integers")
    return {
        "basis": "anonymous_structural_counts_only",
        "website_behavior_verified": False,
        "changes": {key: after[key] - before[key] for key in sorted(fields)},
        "limits": "Equal counts do not prove identical graphs; deltas do not identify the action that caused them."
    }
