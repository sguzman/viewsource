"""Integrity tests for the completed offline research phase."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

class FinalResearchChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = read("specimens/chatgpt-com/v0002/phase5_system_analysis.json")
        cls.record = read("specimens/chatgpt-com/v0002/record.json")
        cls.tasks = [task for task in read("queues/tasks.json")["tasks"]
                     if task["specimen_id"] == "chatgpt-com" and task["version"] == 2]

    def test_terminal_evidence_dispositions(self):
        self.assertEqual(self.record["status"], "researching")
        self.assertEqual(Counter(t["status"] for t in self.tasks), {"done": 69, "not_observable": 22, "queued": 33})
        deep = [t for t in self.tasks if "-followup-deep-" in t["id"]]
        self.assertEqual(Counter(t["status"] for t in deep), {"done": 37, "not_observable": 20})
        refs = {f["evidence"]["evidence_ref"] for f in self.record["findings"]}
        for task in self.tasks:
            if task["status"] == "done":
                self.assertTrue(set(task["evidence_refs"]) <= refs)
            else:
                self.assertTrue(task["notes"])
                self.assertFalse(task.get("evidence_refs"))

    def test_source_scope_and_census(self):
        report = self.report
        ast = report["js_ast"]
        self.assertEqual(ast["files"], 144)
        self.assertEqual(ast["tree_nodes"], 9273632)
        self.assertEqual(ast["static_import_declarations"], 236)
        budget = report["captured_resource_budget"]
        self.assertEqual(budget["scripts"]["bytes"], ast["total_source_bytes"])
        self.assertEqual(sum(item["files"] for item in budget.values()
                             if isinstance(item, dict) and "files" in item), 234)
        self.assertEqual(sum(report["fonts"]["containers"].values()), 60)
        self.assertGreaterEqual(len(report["observability"]["not_observable_from_capture"]), 10)
        refs = {f["evidence"]["evidence_ref"] for f in self.record["findings"]}
        for number in range(51,64):
            self.assertIn("E2-" + str(number).zfill(3), refs)

    def test_export_fields_are_aggregate_only(self):
        report = self.report
        self.assertEqual(report["source_scope"], "saved_archive")
        self.assertIn("privacy", report["methodology"])
        for forbidden in ("capture_url", "account_id", "original_filename",
                          "raw_source", "raw_markup", "unfiltered_headers"):
            self.assertNotIn(forbidden, report)

if __name__ == "__main__":
    unittest.main()
