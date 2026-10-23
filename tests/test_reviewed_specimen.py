"""Integration checks for public reviewed-specimen consistency."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class ReviewedSpecimenChecks(unittest.TestCase):
    def test_first_specimen_review(self):
        specimen = next(
            s for s in read("specimens/index.json")["specimens"]
            if s["id"] == "chatgpt-com"
        )
        self.assertEqual(specimen["status"], "researching")
        self.assertEqual(specimen["current_version"], 2)
        self.assertEqual(specimen["versions"], [1, 2])
        record = read("specimens/chatgpt-com/v0001/record.json")
        self.assertEqual(record["status"], "reviewed")
        self.assertGreaterEqual(len(record["components"]), 60)
        self.assertGreaterEqual(len(record["relationships"]), 70)
        self.assertGreaterEqual(len(record["findings"]), 25)
        self.assertEqual(set(record["coverage"].values()), {"analyzed", "not_observable"})
        tasks = [
            t for t in read("queues/tasks.json")["tasks"]
            if t["specimen_id"] == "chatgpt-com" and t["version"] == 1
        ]
        self.assertEqual(len(tasks), 18)
        self.assertEqual(sum(t["status"] == "done" for t in tasks), 14)
        self.assertEqual(sum(t["status"] == "not_observable" for t in tasks), 4)

    def test_sanitized_inventory_and_gallery(self):
        inventory = read("specimens/chatgpt-com/v0001/resource_inventory.json")
        self.assertEqual(inventory["totals"]["external_references"], 31)
        self.assertEqual(len(inventory["resources"]), 31)
        for item in inventory["resources"]:
            self.assertFalse(item["content_available"])
            self.assertNotIn("url", item)
            self.assertNotIn("path", item)
            self.assertNotIn("filename", item)
        entries = read("gallery/index.json")["entries"]
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["specimen_id"], "chatgpt-com")
        self.assertTrue((ROOT / entries[0]["path"]).is_file())


    def test_second_specimen_review_and_work_queue(self):
        record = read("specimens/chatgpt-com/v0002/record.json")
        self.assertEqual(record["status"], "researching")
        self.assertEqual(record["previous_version"], 1)
        self.assertGreaterEqual(len(record["components"]), 270)
        self.assertGreaterEqual(len(record["findings"]), 36)
        self.assertEqual(set(record["coverage"].values()), {"analyzed", "partial"})
        tasks = [t for t in read("queues/tasks.json")["tasks"]
                 if t["specimen_id"] == "chatgpt-com" and t["version"] == 2]
        initial = [t for t in tasks if "-followup-deep-" not in t["id"]
                   and "-followup-static-" not in t["id"]]
        deep = [t for t in tasks if "-followup-deep-" in t["id"]]
        reopened = [t for t in tasks if "-followup-static-" in t["id"]]
        self.assertEqual(len(reopened), 33)
        self.assertEqual(sum(t["status"] == "queued" for t in reopened), 25)
        self.assertEqual(sum(t["status"] == "in_progress" for t in reopened), 8)
        self.assertEqual(len(initial), 34)
        self.assertEqual(len(deep), 57)
        self.assertEqual(sum(t["status"] == "done" for t in initial), 32)
        self.assertEqual(sum(t["status"] == "not_observable" for t in initial), 2)
        self.assertEqual(sum(t["status"] == "done" for t in deep), 37)
        self.assertEqual(sum(t["status"] == "not_observable" for t in deep), 20)
        by_id = {t["id"]: t for t in tasks}
        for profile in ("followup-dynamic-a11y-paths", "followup-dom-event-graph"):
            item = by_id["chatgpt-com-v0002-" + profile]
            self.assertEqual(item["status"], "not_observable")
            self.assertNotIn("evidence_refs", item)
            self.assertTrue(item["notes"])
        evidence_refs = {f["evidence"]["evidence_ref"] for f in record["findings"]}
        for task in tasks:
            if task["status"] == "done":
                self.assertTrue(task.get("evidence_refs"))
                self.assertTrue(set(task["evidence_refs"]) <= evidence_refs)

    def test_deep_analysis_contains_no_capture_content(self):
        report = read("specimens/chatgpt-com/v0002/deep_analysis.json")
        self.assertEqual(report["network"]["fetch_syntax"]["occurrences"], 186)
        self.assertEqual(report["interaction"]["document"]["buttons"], 130)
        self.assertEqual(report["graphics"]["icon_sprite"]["symbol_definitions"], 911)
        self.assertEqual(report["security"]["markup"]["script_nonce_attributes"], 18)
        self.assertEqual(report["evolution"]["source_scope_difference"]["verified_site_product_changes"], 0)
        contents = json.dumps(report).lower()
        for forbidden in ("http://", "https://", "source-dom.html", "page-snapshot", "session_token", "SYNTHETIC_PRIVATE_USER_SENTINEL"):
            self.assertNotIn(forbidden, contents)


    def test_deep_research_backlog_preserved(self):
        tasks = [t for t in read("queues/tasks.json")["tasks"]
                 if t["specimen_id"] == "chatgpt-com" and t["version"] == 2
                 and "-followup-deep-" in t["id"]]
        self.assertGreaterEqual(len(tasks), 55)
        self.assertEqual(sum(t["status"] == "done" for t in tasks), 37)
        self.assertEqual(sum(t["status"] == "not_observable" for t in tasks), 20)
        self.assertTrue(all(t["notes"] for t in tasks))
        record = read("specimens/chatgpt-com/v0002/record.json")
        self.assertEqual(record["status"], "researching")
        self.assertEqual(record["coverage"]["review"], "partial")


if __name__ == "__main__":
    unittest.main()
