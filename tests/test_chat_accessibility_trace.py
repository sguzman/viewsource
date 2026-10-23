"""Accessible transcript controls in saved source; no runtime claims."""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/"specimens/chatgpt-com/v0002/chat_accessibility_trace.json"

class AccessibleTranscriptTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.study=json.loads(FILE.read_text("utf-8"))

    def test_client_accessibility_source(self):
        d=self.study
        self.assertEqual((d["specimen_id"],d["version"]),("chatgpt-com",2))
        self.assertEqual(set(d["source_refs"]),{"R-JS-066","R-JS-072"})
        self.assertEqual(d["evidence_class"],"observed_static")
        for key in ("captured_app_executed","screen_reader_tested","accessibility_outcome_verified"):
            self.assertFalse(d[key])
        self.assertEqual(len(d["mechanisms"]),8)
        self.assertEqual(len(d["source_relationships"]),7)
        self.assertIn("request_scoped_completion_announcement",
            {m["id"] for m in d["mechanisms"]})
        self.assertIn("abortable_target_navigation",
            {m["id"] for m in d["mechanisms"]})
        self.assertTrue(d["limits"])
        self.assertTrue(all(m["source_ref"] in d["source_refs"] for m in d["mechanisms"]))

    def test_no_original_source_exposed(self):
        text=FILE.read_text("utf-8").lower()
        for forbidden in ("https://","http://",".js","raw_source","bundle-",
                          "authorization:","bearer ","session_token",
                          "page-snapshot","original_filename","private_user"):
            self.assertNotIn(forbidden,text)

if __name__=="__main__":
    unittest.main()
