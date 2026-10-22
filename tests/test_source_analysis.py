"""Verify the privacy-safe ordinal research graph without needing original captures."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class V2SourceAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads((ROOT / "specimens/chatgpt-com/v0002/source_analysis.json").read_text(encoding="utf-8"))
        cls.inventory = json.loads((ROOT / "specimens/chatgpt-com/v0002/resource_inventory.json").read_text(encoding="utf-8"))

    def test_graph_references_existing_ordinals(self):
        graph = self.doc["javascript"]["reference_graph"]
        script_ids = {row["id"] for row in self.inventory["resources"] if row["category"] == "script"}
        edges = set()
        for source, ranges in graph["source_to_target_ranges"].items():
            self.assertIn(source, script_ids)
            for first, last in ranges:
                self.assertLessEqual(first, last)
                for number in range(first, last + 1):
                    target = f"R-JS-{number:03d}"
                    self.assertIn(target, script_ids)
                    self.assertNotEqual(target, source)
                    edges.add((source, target))
        self.assertEqual(len(edges), graph["pairs"])
        self.assertEqual(len({source for source, _ in edges}), graph["source_bundles"])
        self.assertEqual(len({target for _, target in edges}), graph["target_bundles"])

    def test_counts_and_privacy_boundary(self):
        self.assertEqual(self.doc["fonts"]["total_files"], 60)
        self.assertEqual(sum(self.doc["fonts"]["file_counts_by_family"].values()), 60)
        self.assertEqual(self.doc["dom"]["modulepreload_links_resolved_to_captured_assets"], 72)
        self.assertEqual(self.doc["css"]["unique_custom_property_spellings"], 2509)
        self.assertEqual(self.doc["javascript"]["reference_graph"]["pairs"], 300)
        serialized = json.dumps(self.doc).lower()
        for forbidden in ("https://", "http://", "session_token", "conversation_id", "auth_cookie",
                          "source-dom.html", "manifest.json", "SYNTHETIC_PRIVATE_USER_SENTINEL"):
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
