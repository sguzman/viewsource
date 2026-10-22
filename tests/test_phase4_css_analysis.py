"""Consistency checks for the source-limited CSS ontology and aggregate publication."""
from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


class CssResearchChecks(unittest.TestCase):
    def test_custom_property_census(self):
        d = read("specimens/chatgpt-com/v0002/phase4_css_analysis.json")
        p = d["tokens"]
        groups = p["families"]
        self.assertEqual(p["css_files"], 17) if "css_files" in p else None
        self.assertEqual(sum(x["distinct_definitions"] for x in groups.values()), p["distinct_defined_names"])
        self.assertEqual(sum(x["declarations"] for x in groups.values()), p["declaration_occurrences"])
        self.assertEqual(sum(x["references"] for x in groups.values()), p["variable_reference_occurrences"])
        self.assertEqual(p["distinct_referenced_names"],
                         p["distinct_defined_and_referenced"] + p["distinct_referenced_without_a_saved_definition"])

    def test_css_task_closures_are_grounded(self):
        record = read("specimens/chatgpt-com/v0002/record.json")
        evidence = {f["evidence"]["evidence_ref"] for f in record["findings"]}
        tasks = read("queues/tasks.json")["tasks"]
        suffixes = {
            "token-taxonomy": "E2-048",
            "responsive-matrix": "E2-049",
            "motion": "E2-050"
        }
        for suffix, ref in suffixes.items():
            key = "chatgpt-com-v0002-followup-deep-" + suffix
            task = next(t for t in tasks if t["id"] == key)
            self.assertEqual(task["status"], "done")
            self.assertEqual(task["evidence_refs"], [ref])
            self.assertIn(ref, evidence)

    def test_media_scan_denominators_and_limits(self):
        d = read("specimens/chatgpt-com/v0002/phase4_css_analysis.json")
        media = d["responsive"]
        self.assertGreaterEqual(media["lexical_media_at_rules"], media["bounded_media_preludes_examined"])
        self.assertGreaterEqual(media["lexical_container_at_rules"], media["bounded_container_preludes_examined"])
        self.assertEqual(d["motion"]["reduced_motion_media_preludes"], 168)
        self.assertFalse(d["motion"]["runtime_motion_observed"])
        self.assertTrue(d["limitations"])

    def test_css_report_has_no_captured_identifiers(self):
        d = read("specimens/chatgpt-com/v0002/phase4_css_analysis.json")
        text = json.dumps(d)
        self.assertNotRegex(text, r"https?://")
        self.assertNotRegex(text, r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
        self.assertNotRegex(text, r"user-[A-Za-z0-9]{4,}")
        self.assertNotIn("raw_selector", text)
        self.assertNotIn("asset_path", text)
        self.assertNotIn("private_identifier", text)


if __name__ == "__main__":
    unittest.main()
