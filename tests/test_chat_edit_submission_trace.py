"""Source-grounded user-message editing behavior, without server claims."""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/"specimens/chatgpt-com/v0002/chat_edit_submission_trace.json"

class ChatEditSubmissionTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.study=json.loads(FILE.read_text(encoding="utf8"))

    def test_client_edit_sequence(self):
        d=self.study
        self.assertEqual((d["specimen_id"],d["version"]),("chatgpt-com",2))
        self.assertEqual(set(d["source_refs"]),{"R-JS-069","R-JS-072"})
        self.assertEqual(d["evidence_class"],"observed_static")
        for k in ("source_executed","edit_request_completed","server_mutation_verified"):
            self.assertFalse(d[k])
        self.assertEqual(len(d["stages"]),9)
        self.assertEqual(len(d["relationships"]),8)
        stages={item["id"] for item in d["stages"]}
        for k in ("target_message_lookup","edited_prompt_validation",
                  "active_response_stop","context_revalidation",
                  "replacement_completion_submission","busy_cleanup_and_error_feedback"):
            self.assertIn(k,stages)
        self.assertTrue(d["unverified"])
        self.assertTrue(all(x["source_ref"] in d["source_refs"] for x in d["stages"]))

    def test_no_private_source_published(self):
        s=FILE.read_text(encoding="utf8").lower()
        for forbidden in ("https://","http://",".js","bundle-","raw_source",
                          "authorization:","bearer ","session_token",
                          "page-snapshot","original_filename","original_minified_symbol"):
            self.assertNotIn(forbidden,s)

if __name__=="__main__":
    unittest.main()
