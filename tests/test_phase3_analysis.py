"""Regression checks for ordinal-only deep source analysis."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class DeepResearchIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = read("specimens/chatgpt-com/v0002/phase3_analysis.json")
        cls.record = read("specimens/chatgpt-com/v0002/record.json")
        cls.tasks = [t for t in read("queues/tasks.json")["tasks"]
                     if t["specimen_id"] == "chatgpt-com" and t["version"] == 2]

    def test_capture_and_document_accounting(self):
        p = self.report
        self.assertEqual(p["capture"]["archive_entries"],
                         p["capture"]["resource_entries"] + p["capture"]["archive_support_entries"])
        self.assertEqual(p["capture"]["unsuccessful_resource_attempts"],
                         sum(p["capture"][name] for name in
                             ("http_403", "http_404", "other_failed_attempts")))
        self.assertEqual(p["document"]["buttons"],
                         sum(p["document"]["closest_landmark_buttons"].values()))
        self.assertEqual(p["document"]["anchors"],
                         sum(p["document"]["anchor_destination_classes"].values()))
        self.assertEqual(p["load_declarations"]["modulepreload_links"], 72)
        self.assertEqual(p["load_declarations"]["css_link_elements"], 18)
        self.assertEqual(p["load_declarations"]["distinct_css_assets"], 17)

    def test_parsed_import_edges_only_anonymous_ordinals(self):
        graph = self.report["javascript_ast"]
        self.assertEqual(graph["scripts_parsed"], 144)
        self.assertEqual(graph["parse_diagnostics"], 0)
        self.assertEqual(graph["static_import_declarations"], 236)
        self.assertEqual(graph["dynamic_import_expressions"], 18)
        edges = set()
        source = set()
        target = set()
        for src, ranges in graph["source_to_target_ranges"].items():
            self.assertRegex(src, r"^R-JS-\d{3}$")
            index = int(src[-3:])
            self.assertGreaterEqual(index, 1)
            self.assertLessEqual(index, 144)
            source.add(index)
            for low, high in ranges:
                self.assertLessEqual(low, high)
                for dst in range(low, high + 1):
                    self.assertLessEqual(dst, 144)
                    self.assertGreaterEqual(dst, 1)
                    self.assertNotIn((index, dst), edges)
                    edges.add((index, dst))
                    target.add(dst)
        self.assertEqual(len(edges), graph["mapped_static_import_edges"])
        self.assertEqual(len(edges), graph["unique_edge_pairs"])
        self.assertEqual(len(source), graph["source_bundle_count"])
        self.assertEqual(len(target), graph["target_bundle_count"])
        self.assertEqual(sum(a == b for a, b in edges), graph["ordinal_self_edges"])

    def test_sprite_and_research_status(self):
        icons = self.report["icon_linkage"]
        self.assertEqual(icons["dom_svg_use_elements"], icons["svg_uses_matching_sprite_asset"])
        self.assertEqual(icons["dom_svg_use_elements"], icons["svg_uses_matching_symbol_id"])
        self.assertLessEqual(icons["unique_sprite_symbols_referenced"], icons["sprite_symbols"])
        deep = [t for t in self.tasks if "-followup-deep-" in t["id"]]
        self.assertEqual(len(deep), 57)
        self.assertEqual(Counter(t["status"] for t in deep), {"done": 16, "queued": 41})
        evidence = {f["evidence"]["evidence_ref"] for f in self.record["findings"]}
        by_id = {t["id"]: t for t in self.tasks}
        for t in deep:
            self.assertTrue(all(dep in by_id for dep in t["depends_on"]))
            if t["status"] == "done":
                self.assertTrue(set(t["evidence_refs"]) <= evidence)
        self.assertEqual(self.record["status"], "researching")

    def test_only_aggregated_public_output(self):
        p = self.report
        self.assertEqual(p["scope"], "saved_archive")
        self.assertIn("privacy", p)
        serialized = json.dumps(p)
        self.assertIsNone(re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", serialized))
        self.assertIsNone(re.search(r"https?://", serialized))
        self.assertIsNone(re.search(r"user-[a-zA-Z0-9]{4,}", serialized))
        self.assertNotIn("source_path", serialized)
        self.assertNotIn("original_filename", serialized)
        self.assertNotIn("raw_html", serialized)


if __name__ == "__main__":
    unittest.main()
