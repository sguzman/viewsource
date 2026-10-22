"""Protect privacy and evidence scope in the captured static AST report."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "specimens/chatgpt-com/v0002/chat_ast_followup.json"


class ChatAstFollowupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(PATH.read_text("utf-8"))

    def test_evidence_scope(self):
        item = self.data
        self.assertEqual((item["specimen_id"], item["version"]), ("chatgpt-com", 2))
        self.assertEqual(item["source_scope"], "saved_archive")
        self.assertEqual(item["evidence_class"], "observed_static")
        self.assertFalse(item["source_content_published"])
        self.assertFalse(item["live_behavior_verified"])
        self.assertFalse(item["backend_contract_verified"])
        self.assertGreater(item["ast_census"]["parsed_javascript_bundles"], 100)
        self.assertTrue(item["unresolved"])

    def test_only_allowlisted_aggregate_fields_and_no_input_identifiers(self):
        text = PATH.read_text("utf-8")
        for forbidden in (".js", "source-dom.html", "page-snapshot-", "content_parts",
                          "raw_source", "source_filepath", "cookies", "authorization:",
                          "private_user", "session_token"):
            self.assertNotIn(forbidden, text.lower())
        for value in self.data["member_property_cooccurrence_functions"].values():
            self.assertIsInstance(value, int)
            self.assertGreaterEqual(value, 0)
        for value in self.data["member_property_assignment_functions"].values():
            self.assertIsInstance(value, int)
            self.assertGreaterEqual(value, 0)


if __name__ == "__main__":
    unittest.main()
