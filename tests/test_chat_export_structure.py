"""Synthetic tree fixtures for a local, privacy-minimized ChatGPT export parser."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "inspect_chat_export", ROOT / "scripts/inspect_chat_export.py")
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class ChatExportStructureTests(unittest.TestCase):
    def sample(self):
        return {
            "title": "fictional-title",
            "conversation_id": "fictional-conversation-key",
            "mapping": {
                "root": {"parent": None, "children": ["user"], "message": None},
                "user": {"parent": "root", "children": ["reply-a", "reply-b"],
                         "message": {"content": {"parts": ["fictional-only"]}}},
                "reply-a": {"parent": "user", "children": [],
                            "message": {"author": {"role": "assistant"}}},
                "reply-b": {"parent": "user", "children": [],
                            "message": {"author": {"role": "assistant"}}},
            },
            "current_node": "reply-b",
        }

    def test_tree_alternatives_and_visible_path(self):
        item = mod.inspect_conversation(self.sample())
        self.assertEqual(item["shape"], "mapping_tree")
        self.assertEqual(item["nodes"], 4)
        self.assertEqual(item["message_nodes"], 3)
        self.assertEqual(item["null_message_nodes"], 1)
        self.assertEqual(item["branch_points"], 1)
        self.assertEqual(item["alternative_children"], 1)
        self.assertEqual(item["parent_links"], 3)
        self.assertEqual(item["selected_path_length"], 3)
        self.assertEqual(item["off_path_nodes"], 1)
        self.assertEqual(item["selected_path_status"], "resolved")

    def test_duplicate_children_are_not_counted_as_alternatives(self):
        item = self.sample()
        item["mapping"]["user"]["children"] = ["reply-a", "reply-a", "reply-b"]
        metrics = mod.inspect_conversation(item)
        self.assertEqual(metrics["duplicate_child_links"], 1)
        self.assertEqual(metrics["branch_points"], 1)
        self.assertEqual(metrics["alternative_children"], 1)

    def test_nonstring_children_do_not_count_as_branches(self):
        item = self.sample()
        item["mapping"]["user"]["children"] = ["reply-a", ["bad"], "reply-b"]
        metrics = mod.inspect_conversation(item)
        self.assertGreater(metrics["dangling_child_links"], 0)
        self.assertEqual(metrics["alternative_children"], 1)

    def test_selected_branch_switch_does_not_change_node_count(self):
        original = self.sample()
        alternative = self.sample()
        alternative["current_node"] = "reply-a"
        first = mod.inspect_conversation(original)
        second = mod.inspect_conversation(alternative)
        self.assertEqual(first["nodes"], second["nodes"])
        self.assertEqual(first["branch_points"], second["branch_points"])
        self.assertEqual(first["selected_path_length"], second["selected_path_length"])

    def test_unknown_current_does_not_choose_arbitrary_child(self):
        item = self.sample()
        item["current_node"] = "not-a-node"
        metrics = mod.inspect_conversation(item)
        self.assertEqual(metrics["selected_path_status"], "dangling")
        self.assertIsNone(metrics["selected_path_length"])
        self.assertIsNone(metrics["off_path_nodes"])

    def test_parent_child_mismatch_reported_not_repaired(self):
        item = self.sample()
        item["mapping"]["reply-b"]["parent"] = "root"
        metrics = mod.inspect_conversation(item)
        self.assertGreater(metrics["parent_child_conflicts"], 0)

    def test_cycle_rejected_for_selected_path(self):
        item = self.sample()
        item["mapping"]["root"]["parent"] = "reply-b"
        metrics = mod.inspect_conversation(item)
        self.assertGreater(metrics["ancestry_cycles"], 0)
        self.assertEqual(metrics["selected_path_status"], "cycle")

    def test_flat_format_is_not_invented_as_tree(self):
        result = mod.inspect_export([{"messages": [
            {"content": "private-synthetic-placeholder"},
            {"other": "unstructured"}
        ]}])
        self.assertEqual(result["shapes"]["flat_messages_no_tree"], 1)
        self.assertEqual(result["structural_counts"]["flat_message_items"], 2)
        self.assertEqual(result["structural_counts"]["nodes"], 0)
        self.assertEqual(result["structural_counts"]["parent_links"], 0)
        self.assertEqual(result["structural_counts"]["branch_points"], 0)
        self.assertEqual(result["selection_status"]["not_available"], 1)
        self.assertNotIn("private-synthetic-placeholder", json.dumps(result))

    def test_only_aggregated_structure_is_returned(self):
        a = self.sample()
        output = mod.inspect_export([a, self.sample()])
        text = json.dumps(output)
        self.assertEqual(output["conversation_count"], 2)
        self.assertEqual(output["resolved_off_path_nodes_total"], 2)
        for private_placeholder in ("fictional-title", "fictional-conversation-key",
                                    "fictional-only", "reply-a", "reply-b"):
            self.assertNotIn(private_placeholder, text)
        self.assertFalse(output["live_chat_implementation_verified"])

    def test_wrong_container_is_not_coerced(self):
        with self.assertRaises(mod.ExportShapeError):
            mod.inspect_export({"mapping": {}})


    def test_incremental_reader_with_small_chunks(self):
        from io import StringIO
        payload=json.dumps([self.sample(), self.sample()], ensure_ascii=False)
        parsed=list(mod.iter_export_records(StringIO(payload),chunk_size=3))
        self.assertEqual(len(parsed),2)
        summary=mod.summarize_records(
            mod.iter_export_records(StringIO(payload),chunk_size=5))
        self.assertEqual(summary["conversation_count"],2)
        self.assertEqual(summary["resolved_off_path_nodes_total"],2)
        self.assertNotIn("fictional-title",json.dumps(summary))

    def test_scanner_handles_nested_strings_and_many_chunk_boundaries(self):
        from io import StringIO
        records = [
            {"content": {"parts": ['brackets ] } commas , [ " and backslash \\']},
             "mapping": {"root": {"parent": None, "children": [], "message": None}},
             "current_node": "root"},
            {"messages": [{"body": "fictional" * 3000}, {"body": "[{},]"}]},
            {"mixed": [1, {"items": [True, False, None]}, "plain synthetic text"]},
        ]
        payload = json.dumps(records, ensure_ascii=False)
        expected = mod.inspect_export(records)
        for size in (1, 2, 3, 11, 127, 1024, 65536):
            with self.subTest(chunk_size=size):
                actual = mod.summarize_records(
                    mod.iter_export_records(StringIO(payload), chunk_size=size))
                self.assertEqual(actual, expected)

    def test_scanner_refuses_invalid_records_without_retrying_fragments(self):
        from io import StringIO
        for payload in (
            '[{"nested":[1,2}],{"a":1,"a":2}]',
            '[{"text":"unfinished}]',
            '[{"text":"escaped\\\\quote"},,{}]',
            ' [1, 2] trailing ',
        ):
            with self.subTest(payload=payload[:30]), self.assertRaises(ValueError):
                list(mod.iter_export_records(StringIO(payload), chunk_size=3))

    def test_stream_reader_rejects_truncated_and_extra_data(self):
        from io import StringIO
        for payload in ('[{},]', '[{}] trailing', '{ }', '[{"partial":'):
            with self.subTest(kind=payload[:3]), self.assertRaises(mod.ExportShapeError):
                list(mod.iter_export_records(StringIO(payload),chunk_size=2))

    def test_stream_reader_rejects_non_json_unicode_whitespace(self):
        from io import StringIO
        for payload in ("\u00a0[]", "[]\u2003", "[{}\u00a0]"):
            with self.subTest(payload=repr(payload)), self.assertRaises(ValueError):
                list(mod.iter_export_records(StringIO(payload), chunk_size=1))

    def test_stream_reader_rejects_unbounded_read_sizes(self):
        from io import StringIO
        for size in (0, -1, True, 2**25):
            with self.subTest(size=size), self.assertRaises(mod.ExportShapeError):
                list(mod.iter_export_records(StringIO("[]"), chunk_size=size))

    def test_stream_reader_rejects_duplicate_keys_and_nonfinite_literals(self):
        from io import StringIO
        for payload in (
            '[{"mapping":{}, "mapping":{}}]',
            '[{"outer":{"id":1,"id":2}}]',
            '[{"value":NaN}]', '[{"value":Infinity}]',
            '[{"value":-Infinity}]',
        ):
            with self.subTest(payload=payload[:24]), self.assertRaises(mod.ExportShapeError):
                list(mod.iter_export_records(StringIO(payload), chunk_size=2))

    def test_stream_reader_accepts_empty_and_whitespace_arrays(self):
        from io import StringIO
        self.assertEqual(list(mod.iter_export_records(StringIO(" [   ] \n"))),[])
        self.assertEqual(mod.summarize_records(iter(()))["conversation_count"],0)


if __name__ == "__main__":
    unittest.main()
