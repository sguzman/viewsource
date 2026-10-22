"""Source/status crosswalk for named chat operations."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "specimens/chatgpt-com/v0002"


class CapabilityMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads((BASE / "chat_capability_matrix.json").read_text("utf-8"))
        cls.graph = json.loads((BASE / "chat-interaction.graph.json").read_text("utf-8"))
        cls.documentation = json.loads((BASE / "public_chat_actions.json").read_text("utf-8"))
        cls.record = json.loads((BASE / "record.json").read_text("utf-8"))

    def test_references_exist_and_all_runtime_unknown(self):
        refs = {f["evidence"]["evidence_ref"] for f in self.record["findings"]}
        events = {e["id"] for e in self.graph["events"]}
        relations = {r["id"] for r in self.graph["domain_relations"]}
        docs = {a["id"] for a in self.documentation["actions"]}
        rows = self.matrix["capabilities"]
        self.assertEqual(len(rows), 8)
        self.assertEqual(len({x["id"] for x in rows}), 8)
        for row in rows:
            self.assertEqual(row["runtime_status"], "not_verified")
            self.assertTrue(set(row["static_refs"]) <= refs)
            self.assertTrue(set(row["candidate_events"]) <= events)
            self.assertTrue(set(row["candidate_relations"]) <= relations)
            self.assertTrue(row["documented_action"] is None or row["documented_action"] in docs)
            self.assertTrue(row["next_experiment"])
            self.assertTrue(row["static_refs"] or row["documented_action"])

    def test_branching_ui_documented_without_capture_claim(self):
        branch = next(x for x in self.matrix["capabilities"] if x["id"] == "branch_new_chat")
        self.assertEqual(branch["static_refs"], [])
        self.assertEqual(branch["documented_action"], "branch_new_chat")
        self.assertEqual(branch["candidate_relations"], ["chat-fork"])
        self.assertEqual(branch["runtime_status"], "not_verified")

    def test_no_identifier_or_protocol_data(self):
        text = json.dumps(self.matrix)
        for key in ("conversation_id", "request_body", "session_token",
                    "message_content", "authorization", "cookie_value"):
            self.assertNotIn('"'+key+'"', text)


if __name__ == "__main__":
    unittest.main()
