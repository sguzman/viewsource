"""Trace evidence must be reproducible, anonymous and explicitly source-scoped."""
from __future__ import annotations
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "specimens/chatgpt-com/v0002/chat_static_impl_trace.json"


class ChatImplementationTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text("utf-8"))

    def test_counts_and_ordinals(self):
        doc = self.data
        self.assertEqual(doc["asset_files_parsed"], 144)
        self.assertEqual(doc["parse_failures"], 0)
        self.assertEqual(doc["match_count"], len(doc["matches"]))
        self.assertEqual(sum(doc["patterns"].values()), len(doc["matches"]))
        keys = [(item["source_ref"], item["function_ordinal"], item["pattern"])
                for item in doc["matches"]]
        self.assertEqual(len(set(keys)), len(keys))
        self.assertEqual(len({(k[0], k[1]) for k in keys}), doc["matched_functions"])
        self.assertEqual(len({k[0] for k in keys}), doc["matched_source_bundles"])
        for item in doc["matches"]:
            self.assertRegex(item["source_ref"], r"^R-JS-[0-9]{3}$")
            self.assertGreater(item["function_ordinal"], 0)
            self.assertFalse(item["domain_ownership_verified"])

    def test_manual_findings_anchor_in_syntactic_results(self):
        doc = self.data
        present = {(x["source_ref"], x["function_ordinal"]) for x in doc["matches"]}
        for item in doc["reviewed_client_operations"]:
            self.assertIn((item["source_ref"], item["function_ordinal"]), present)
            self.assertEqual(item["evidence_class"], "observed_static")
            self.assertTrue(item["limits"])
        self.assertFalse(doc["verified_live_behavior"])
        self.assertFalse(doc["server_contract_verified"])
        self.assertTrue(doc["open_static_questions"])

    def test_reviewed_export_getters_do_not_claim_runtime_calls(self):
        doc = self.data
        present = {(x["source_ref"], x["function_ordinal"]) for x in doc["matches"]}
        self.assertEqual(len(doc["reviewed_module_exports"]), 7)
        for item in doc["reviewed_module_exports"]:
            self.assertRegex(item["source_ref"], r"^R-JS-[0-9]{3}$")
            self.assertGreater(item["exported_function_ordinal"], 0)
            self.assertEqual(item["export_kind"], "static_module_getter")
            self.assertGreater(item["module_factory_ordinal"], 0)
        self.assertTrue(doc["module_export_limitations"])

    def test_same_factory_calls_share_one_source_and_dispatcher(self):
        calls = self.data["reviewed_direct_calls"]
        self.assertEqual(len(calls), 4)
        self.assertEqual({x["caller_role"] for x in calls}, {
            "completion_submission", "local_function_result_submission",
            "regeneration_submission", "conditional_retry_submission"
        })
        for call in calls:
            self.assertEqual(call["source_ref"], "R-JS-018")
            self.assertEqual(call["module_factory_ordinal"], 9012)
            self.assertEqual(call["callee_function_ordinal"], 9032)
            self.assertEqual(call["call_kind"], "same_factory_direct_identifier_call")
            self.assertEqual(call["evidence_class"], "observed_static")

    def test_detected_direct_calls_are_broader_than_reviewed_subset(self):
        doc = self.data
        detected = {(x["source_ref"], x["caller_function_ordinal"],
                     x["callee_function_ordinal"]) for x in doc["candidate_direct_calls"]}
        reviewed = {(x["source_ref"], x["caller_function_ordinal"],
                     x["callee_function_ordinal"]) for x in doc["reviewed_direct_calls"]}
        self.assertEqual(len(detected), 6)
        self.assertEqual(len(reviewed), 4)
        self.assertTrue(reviewed <= detected)
        self.assertEqual(len(detected - reviewed), doc["unreviewed_direct_call_count"])
        self.assertTrue(all(x["link_status"] == "candidate_named_direct_call"
                            for x in doc["candidate_direct_calls"]))

    def test_report_does_not_publish_source_paths_or_chat_content(self):
        text = DATA.read_text("utf-8").lower()
        for term in ("http://", "https://", ".js", "bundle-", "source-dom",
                     "authorization:", "access_token", "message_content",
                     "conversation_id=", "raw_source", "source_offset",
                     "page-snapshot-chatgpt"):
            self.assertNotIn(term, text)


if __name__ == "__main__":
    unittest.main()
