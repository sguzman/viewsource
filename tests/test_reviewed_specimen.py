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
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["specimen_id"], "chatgpt-com")
        self.assertTrue((ROOT / entries[0]["path"]).is_file())


if __name__ == "__main__":
    unittest.main()
