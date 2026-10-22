"""Synthetic export trees normalized without emitting source identifiers."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "normalize_chat_export", ROOT / "scripts/normalize_chat_export.py")
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class ExportGraphNormalizationTests(unittest.TestCase):
    def example(self):
        # Deliberately unsorted to test topological ordering.
        return {
            "conversation_id": "fictional-only-conversation",
            "title": "fictional-only-title",
            "current_node": "reply-z",
            "mapping": {
                "reply-z": {"parent": "prompt", "children": [],
                            "message": {"author": {"role": "assistant"}}},
                "root": {"parent": None, "children": ["prompt"], "message": None},
                "reply-a": {"parent": "prompt", "children": [],
                            "message": {"author": {"role": "assistant"}}},
                "prompt": {"parent": "root", "children": ["reply-a", "reply-z"],
                           "message": {"author": {"role": "user"},
                                       "content": {"parts": ["invented-text"]}}},
            },
        }

    def test_selected_branch_and_parent_links(self):
        tree = mod.normalize_conversation(self.example())
        self.assertEqual(tree["node_count"], 4)
        self.assertEqual(tree["branch_point_count"], 1)
        self.assertEqual(tree["alternative_child_count"], 1)
        self.assertEqual(len(tree["selected_path"]), 3)
        self.assertEqual(tree["selected_path"][0], "n0001")
        self.assertEqual(tree["nodes"][0]["parent"], None)
        self.assertEqual(tree["nodes"][1]["parent"], "n0001")
        self.assertTrue(all(n["parent"] == "n0002" for n in tree["nodes"][2:]))
        self.assertEqual(tree["nodes"][1]["actor"], "user")
        self.assertFalse(tree["live_implementation_verified"])

    def test_internal_selected_node_is_represented_without_guessing_leaf(self):
        item = self.example()
        item["current_node"] = "prompt"
        result = mod.normalize_conversation(item)
        self.assertEqual(len(result["selected_path"]), 2)
        self.assertEqual(result["branch_point_count"], 1)

    def test_structural_output_drops_all_original_labels(self):
        item = self.example()
        result = mod.normalize_conversation(item)
        output = json.dumps(result)
        for secret_placeholder in (
            "fictional-only-conversation", "fictional-only-title",
            "invented-text", "reply-z", "reply-a", "prompt",
        ):
            self.assertNotIn(secret_placeholder, output)

    def test_missing_selected_node_refused(self):
        item = self.example()
        item["current_node"] = "not-present"
        with self.assertRaises(mod.ExportGraphError):
            mod.normalize_conversation(item)

    def test_bad_reciprocal_links_refused(self):
        item = self.example()
        item["mapping"]["reply-z"]["parent"] = "root"
        with self.assertRaises(mod.ExportGraphError):
            mod.normalize_conversation(item)

    def test_cycles_refused(self):
        item = self.example()
        item["mapping"]["root"]["parent"] = "reply-z"
        with self.assertRaises(mod.ExportGraphError):
            mod.normalize_conversation(item)

    def test_duplicate_child_link_refused_even_when_parent_matches(self):
        item = self.example()
        item["mapping"]["prompt"]["children"].append("reply-z")
        with self.assertRaises(mod.ExportGraphError):
            mod.normalize_conversation(item)

    def test_nonstring_child_refused(self):
        item = self.example()
        item["mapping"]["prompt"]["children"].append({"not": "a node"})
        with self.assertRaises(mod.ExportGraphError):
            mod.normalize_conversation(item)

    def test_flat_list_not_turned_into_invented_tree(self):
        with self.assertRaises(mod.ExportGraphError):
            mod.normalize_conversation({"messages": [{"actor": "assistant"}]})


if __name__ == "__main__":
    unittest.main()
