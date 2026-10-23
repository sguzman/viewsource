"""Ensure the transcript trace is source-scoped, internally connected and content-free."""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "specimens/chatgpt-com/v0002/chat_transcript_render_trace.json"

class TranscriptRenderTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(FILE.read_text("utf8"))

    def test_source_coverage(self):
        doc = self.doc
        self.assertEqual((doc["specimen_id"], doc["version"]), ("chatgpt-com",2))
        self.assertFalse(doc["runtime_render_verified"])
        self.assertFalse(doc["server_render_contract_verified"])
        self.assertEqual({x["ref"] for x in doc["source_resources"]},
                         {"R-JS-018","R-JS-069","R-JS-072"})
        self.assertEqual(len(doc["stages"]), 7)
        self.assertEqual(len(doc["reviewed_relationships"]), 10)
        cross=doc["verified_cross_module_call"]
        self.assertEqual((cross["source_ref"],cross["target_ref"]),("R-JS-072","R-JS-069"))
        self.assertEqual(cross["kind"],"direct_imported_component_call")
        self.assertEqual(cross["evidence_class"],"observed_static")
        self.assertTrue(cross["boundary"])
        self.assertTrue(doc["unverified"])
        stages = {x["id"] for x in doc["stages"]}
        self.assertIn("dom_message_identity_wrapper", stages)
        self.assertIn("turn_props_and_filters", stages)
        for stage in doc["stages"]:
            self.assertIn(stage["source_ref"], {x["ref"] for x in doc["source_resources"]})
            self.assertEqual(stage["status"], "reviewed")

    def test_no_source_or_private_data(self):
        text = FILE.read_text("utf8").lower()
        for forbidden in ("https://","http://","authorization:", "bearer ",
                          "raw_source",".js","page-snapshot","webpack_modules",
                          "session_token","original_filename","source_text"):
            self.assertNotIn(forbidden,text)

if __name__ == "__main__":
    unittest.main()
