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
