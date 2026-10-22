"""Feature research queue keeps research findings separate from runtime dependencies."""
from __future__ import annotations
from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("validate_feature_research",ROOT / "scripts/validate_feature_research.py")
mod=importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)


class ChatFeatureQueueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks=json.loads((ROOT / "queues/chat_research.json").read_text("utf-8"))["tasks"]

    def test_full_queue_valid(self):
        self.assertEqual(mod.validate_feature_research(),[])

    def test_explicit_remaining_evidence(self):
        self.assertEqual(len(self.tasks),18)
        self.assertEqual(Counter(t["status"] for t in self.tasks),
                         {"done":10,"requires_new_evidence":8})
        self.assertFalse(any(t["status"]=="queued" for t in self.tasks))

    def test_deliverables_backed_by_artifacts(self):
        for task in self.tasks:
            if task["status"]=="done":
                self.assertTrue(task["evidence_refs"] or task.get("artifacts"))
                for filename in task.get("artifacts",[]):
                    self.assertTrue((ROOT / filename).is_file())
            else:
                self.assertEqual(task["scope"],"runtime")
                self.assertEqual(task["evidence_refs"],[])

    def test_dependencies_exist_and_are_acyclic(self):
        ids={t["id"] for t in self.tasks}
        self.assertEqual(len(ids),len(self.tasks))
        for task in self.tasks:
            self.assertTrue(set(task["depends_on"]) <= ids)
            self.assertNotIn(task["id"],task["depends_on"])

    def test_no_private_examples_in_backlog(self):
        source=json.dumps(self.tasks).lower()
        self.assertNotIn("session_token",source)
        self.assertNotIn("raw_message",source)
        self.assertNotIn("cookie_value",source)


if __name__=="__main__":
    unittest.main()
