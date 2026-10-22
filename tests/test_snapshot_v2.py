"""Structural checks for the larger, non-redistributed capture version."""
from pathlib import Path
import json
import unittest
ROOT=Path(__file__).resolve().parents[1]
def read(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))
class SecondSnapshot(unittest.TestCase):
    def test_versions_and_queue(self):
        site=next(s for s in read("specimens/index.json")["specimens"] if s["id"]=="chatgpt-com")
        self.assertEqual(site["versions"],[1,2])
        self.assertEqual(site["current_version"],2)
        rec=read("specimens/chatgpt-com/v0002/record.json")
        self.assertEqual((rec["version"],rec["previous_version"]),(2,1))
        self.assertEqual(rec["capture_scope"],"saved_archive")
        tasks=[t for t in read("queues/tasks.json")["tasks"] if t["specimen_id"]=="chatgpt-com" and t["version"]==2]
        self.assertEqual(len(tasks),34)
        self.assertEqual(len([t for t in tasks if t["profile"]=="followup"]),16)
    def test_sanitized_census(self):
        inv=read("specimens/chatgpt-com/v0002/resource_inventory.json")
        self.assertEqual(len(inv["resources"]),234)
        self.assertEqual(inv["totals"]["missing_reported"],29)
        self.assertEqual(sum(inv["totals"]["captured_by_category"].values()),234)
        self.assertTrue(all(not a["content_committed"] for a in inv["resources"]))
        self.assertTrue(all(not(set(a)&{"path","url","source","text","filename","bytes"}) for a in inv["resources"]))
        self.assertEqual(len(set(a["id"] for a in inv["resources"])),234)
if __name__=="__main__":unittest.main()
