"""ID-independent, content-free export topology comparison tests."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_chat_export import normalize_conversation
from compare_chat_topologies import TopologyError, compare_normalized_trees


def sample():
    return {
        "conversation_id": "secret-conversation-placeholder",
        "current_node": "reply-b",
        "mapping": {
            "reply-b": {"parent": "question", "children": [],
                        "message": {"author": {"role": "assistant"}}},
            "root": {"parent": None, "children": ["question"], "message": None},
            "question": {"parent": "root", "children": ["reply-a", "reply-b"],
                         "message": {"author": {"role": "user"}}},
            "reply-a": {"parent": "question", "children": [],
                        "message": {"author": {"role": "assistant"}}},
        },
    }


class CompareTopologyTests(unittest.TestCase):
    def test_reordered_renamed_identical_tree(self):
        a = normalize_conversation(sample())
        b = sample()
        keys = {"root": "x", "question": "y", "reply-a": "z", "reply-b": "w"}
        b["current_node"] = "w"
        b["mapping"] = {
            keys[key]: {**value,
                        "parent": keys[value["parent"]] if value["parent"] else None,
                        "children": [keys[child] for child in value["children"]]}
            for key, value in reversed(list(b["mapping"].items()))
        }
        out = compare_normalized_trees(a, normalize_conversation(b))
        self.assertTrue(out["unmarked_structure_equivalent"])
        self.assertTrue(out["selection_marked_structure_equivalent"])
        self.assertTrue(all(delta == 0 for delta in out["metric_deltas"].values()))
        self.assertFalse(out["message_identity_correlated"])

    def test_indistinguishable_siblings_are_not_claimed_identical(self):
        before = sample()
        after = sample()
        after["current_node"] = "reply-a"
        out = compare_normalized_trees(
            normalize_conversation(before), normalize_conversation(after))
        self.assertTrue(out["selection_marked_structure_equivalent"])
        self.assertIn("Isomorphic siblings", " ".join(out["limitations"]))

    def test_selection_change_on_asymmetric_branches(self):
        before = sample()
        before["mapping"]["reply-a"]["children"] = ["follow-up"]
        before["mapping"]["follow-up"] = {
            "parent": "reply-a", "children": [],
            "message": {"author": {"role": "user"}},
        }
        after = copy.deepcopy(before)
        after["current_node"] = "follow-up"
        before["current_node"] = "reply-b"
        out = compare_normalized_trees(
            normalize_conversation(before), normalize_conversation(after))
        self.assertTrue(out["unmarked_structure_equivalent"])
        self.assertFalse(out["selection_marked_structure_equivalent"])

    def test_internal_selection_is_valid(self):
        before = sample()
        before["current_node"] = "question"
        out = compare_normalized_trees(
            normalize_conversation(before), normalize_conversation(before))
        self.assertTrue(out["selection_marked_structure_equivalent"])
        self.assertEqual(out["metric_deltas"]["selected_path_length"], 0)

    def test_addition_is_structural_not_attributed_to_an_action(self):
        before = sample()
        after = copy.deepcopy(before)
        after["mapping"]["reply-b"]["children"] = ["new"]
        after["mapping"]["new"] = {
            "parent": "reply-b", "children": [],
            "message": {"author": {"role": "assistant"}},
        }
        after["current_node"] = "new"
        out = compare_normalized_trees(
            normalize_conversation(before), normalize_conversation(after))
        self.assertFalse(out["unmarked_structure_equivalent"])
        self.assertEqual(out["metric_deltas"]["nodes"], 1)
        self.assertFalse(out["live_behavior_verified"])
        self.assertNotIn("secret-conversation-placeholder", json.dumps(out))

    def test_rejects_invalid_graph_and_does_not_echo_data(self):
        before = normalize_conversation(sample())
        for field, value in (
            ("node_count", 2), ("selected_path", ["secret-private"]),
            ("branch_point_count", 5), ("live_implementation_verified", True),
        ):
            altered = copy.deepcopy(before)
            altered[field] = value
            with self.subTest(field=field), self.assertRaises(TopologyError) as cm:
                compare_normalized_trees(altered, before)
            self.assertNotIn("secret-private", str(cm.exception))

    def test_refuses_cyclic_ordinal_graph(self):
        graph = normalize_conversation(sample())
        graph["nodes"][0]["parent"] = graph["nodes"][-1]["ordinal"]
        with self.assertRaises(TopologyError):
            compare_normalized_trees(graph, graph)

    def test_deep_graph_is_iterative_not_recursive(self):
        count = 1600
        graph = {
            "format_version": 1, "source": "local_export_tree",
            "live_implementation_verified": False,
            "node_count": count,
            "nodes": [
                {"ordinal": f"n{i:04d}",
                 "parent": f"n{i-1:04d}" if i > 1 else None,
                 "actor": "user" if i % 2 else "assistant"}
                for i in range(1, count + 1)
            ],
            "selected_path": [f"n{i:04d}" for i in range(1, count + 1)],
            "selected_path_status": "resolved",
            "branch_point_count": 0, "alternative_child_count": 0,
        }
        result = compare_normalized_trees(graph, copy.deepcopy(graph))
        self.assertTrue(result["unmarked_structure_equivalent"])
        self.assertTrue(result["selection_marked_structure_equivalent"])


if __name__ == "__main__":
    unittest.main()
