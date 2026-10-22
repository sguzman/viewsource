"""Tests for public library identification and the anonymized page map."""
from __future__ import annotations

from pathlib import Path
import json
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]

class TechnologyInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT / "specimens/chatgpt-com/v0002/technology_inventory.json").read_text("utf-8"))
        cls.record=json.loads((ROOT / "specimens/chatgpt-com/v0002/record.json").read_text("utf-8"))
        cls.story=json.loads((ROOT / "site/story.json").read_text("utf-8"))

    def test_framework_and_library_evidence(self):
        items=self.data["technologies"]
        by_id={item["id"]:item for item in items}
        self.assertEqual(len(items), len(by_id))
        self.assertEqual(len(items),11)
        for id in ("react","react-router","tailwind-css","radix-ui","prosemirror","katex"):
            self.assertEqual(by_id[id]["confidence"],"strong")
        for item in items:
            self.assertIn(item["confidence"],{"strong","likely","indicator"})
            self.assertTrue(item["evidence"] and item["note"] and item["role"])
            self.assertIsNone(item["version"])
            self.assertTrue(item["observations"])
            for marker in item["observations"]:
                self.assertGreater(marker["matches"],0)
                self.assertGreater(marker["files"],0)
                self.assertGreaterEqual(marker["matches"],marker["files"])

    def test_page_map_has_nested_observed_regions(self):
        data=self.data["page_map"]
        regions={node["id"]:node for node in data["nodes"]}
        self.assertEqual(len(regions),7)
        self.assertEqual(regions["sidebar"]["counts"]["buttons"],74)
        self.assertEqual(regions["top-nav"]["parent"],"sidebar")
        self.assertEqual(regions["list-nav"]["parent"],"sidebar")
        self.assertEqual(regions["main"]["counts"]["buttons"],51)
        self.assertEqual(regions["composer"]["counts"]["file_inputs"],4)
        self.assertEqual(regions["dialog"]["counts"]["buttons"],4)
        self.assertTrue(data["note"])

    def test_public_data_and_navigation(self):
        assert self.data["capture_scope"]=="saved_archive"
        ids={chapter["id"] for chapter in self.story["chapters"]}
        self.assertIn("stack",ids)
        self.assertIn("page-map",ids)
        refs={finding["evidence"]["evidence_ref"] for finding in self.record["findings"]}
        self.assertIn("E2-064",refs)
        self.assertIn("E2-065",refs)
        for chapter in self.story["chapters"]:
            self.assertTrue(set(chapter["evidence"]) <= refs)
        serialized=json.dumps(self.data)
        self.assertNotRegex(serialized,r"https?://")
        self.assertNotRegex(serialized,r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}")
        self.assertNotRegex(serialized,r"user-[a-zA-Z0-9]{4,}")
        self.assertNotIn("raw_source",serialized)
        self.assertNotIn("account_identifier",serialized)

if __name__=="__main__":
    unittest.main()
