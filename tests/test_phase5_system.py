"""Final offline specimen research integrity and source-privacy boundaries."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class FinalSourceScopeChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = read("specimens/chatgpt-com/v0002/phase5_system_analysis.json")
        cls.record = read("specimens/chatgpt-com/v0002/record.json")
        cls.tasks = [t for t in read("queues/tasks.json")["tasks"]
                     if t["specimen_id"] == "chatgpt-com" and t["version"] == 2]

    def test_reviewed_but_source_bounded(self):
        self.assertEqual(self.record["status"], "reviewed")
        deep = [t for t in self.tasks if "-followup-deep-" in t["id"]]
        self.assertEqual(len(deep), 57)
        self.assertEqual(Counter(t["status"] for t in deep), {"done": 37, "not_observable": 20})
        self.assertEqual(Counter(t["status"] for t in self.tasks), {"done": 69, "not_observable": 22})
        self.assertFalse(any(t["status"] == "queued" for t in self.tasks))
        refs = {f["evidence"]["evidence_ref"] for f in self.record["findings"]}
        for task in self.tasks:
            self.assertTrue(task["depends_on"] is not None)
            if task["status"] == "not_observable":
                self.assertTrue(task.get("notes"))
                self.assertFalse(task.get("evidence_refs"))
            else:
                self.assertTrue(task.get("evidence_refs"))
                self.assertTrue(set(task["evidence_refs"]) <= refs)

    def test_source_counts_and_capture_budget(self):
        report = self.report
        ast = report["js_ast"]
        self.assertEqual(ast["files"], 144)
        self.assertEqual(ast["tree_nodes"], 9273632)
        self.assertEqual(ast["static_import_declarations"], 236)
        self.assertEqual(ast["dynamic_import_expressions"], 18)
        budget = report["captured_resource_budget"]
        self.assertEqual(budget["scripts"]["bytes"], ast["total_source_bytes"])
        self.assertAlmostEqual(budget["largest_five_script_share"], 0.3638, places=4)
        self.assertEqual(sum(v["files"] for v in budget.values() if isinstance(v, dict) and "files" in v), 234)
        overlap = report["document_css"]
        self.assertLessEqual(overlap["dom_elements_with_at_least_one_plain_css_class_overlap"], overlap["elements_with_css_classes"])
        self.assertLessEqual(overlap["distinct_overlap_class_names"], overlap["distinct_dom_classes"])
        self.assertEqual(sum(report["fonts"]["semantic_groups"].values()), report["fonts"]["files"])
        self.assertEqual(sum(report["fonts"]["containers"].values()), report["fonts"]["files"])

    def test_observability_is_explicit(self):
        obs = self.report["observability"]
        self.assertGreaterEqual(len(obs["not_observable_from_capture"]), 10)
        self.assertTrue(self.report["limits"])
        for id in range(51,64):
            self.assertIn("E2-"+str(id), {f["evidence"]["evidence_ref"] for f in self.record["findings"]})

    def test_public_report_contains_no_private_evidence(self):
        content = (ROOT / "specimens/chatgpt-com/v0002/phase5_system_analysis.json").read_text("utf-8")
        self.assertNotRegex(content, r"https?://")
        self.assertNotRegex(content, r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
        self.assertNotRegex(content, r"user-[A-Za-z0-9]{4,}")
        for key in ("original_filename", "captured_query", "raw_html", "account_value", "source_path", "capture_manifest"):
            self.assertNotIn('"'+key+'"', content)


if __name__ == "__main__":
    unittest.main()
