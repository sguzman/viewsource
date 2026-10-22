"""Check proposed ChatGPT runtime research protocols stay evidence-bounded."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RuntimeProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = json.loads((ROOT / "queues/chat_runtime_protocols.json").read_text("utf-8"))
        cls.queue = json.loads((ROOT / "queues/chat_research.json").read_text("utf-8"))

    def test_one_proposal_per_unresolved_runtime_task(self):
        expected = {x["id"] for x in self.queue["tasks"]
                    if x["status"] == "requires_new_evidence"}
        actual = [x["task_id"] for x in self.record["protocols"]]
        self.assertEqual(len(actual), len(expected))
        self.assertEqual(set(actual), expected)

    def test_all_outcomes_remain_proposals_with_fixed_structure(self):
        self.assertEqual(self.record["scope"],
                         "proposal_only_requires_separate_explicit_disposable_session_authorization")
        for entry in self.record["protocols"]:
            self.assertEqual(set(entry), {"task_id", "question", "discriminators",
                                          "observables", "stop_condition", "evidence_status"})
            self.assertEqual(entry["evidence_status"], "proposal_only")
            self.assertGreaterEqual(len(entry["discriminators"]), 2)
            self.assertTrue(entry["observables"])
            for x in entry["discriminators"] + entry["observables"]:
                self.assertIsInstance(x, str)
                self.assertTrue(x)
            self.assertTrue(entry["stop_condition"])

    def test_no_selector_or_live_capture_fields(self):
        forbidden = {"message", "contents", "headers", "cookies", "token",
                     "secret", "raw_request", "selector", "trace", "route_literal"}
        for entry in self.record["protocols"]:
            self.assertTrue(forbidden.isdisjoint(set(entry)))


if __name__ == "__main__":
    unittest.main()
