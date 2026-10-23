"""Source-backed response version controls and optimistic selection trace."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"specimens/chatgpt-com/v0002/chat_branch_switch_trace.json"

class SavedBranchSwitchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.study=json.loads(PATH.read_text(encoding="utf-8"))

    def test_response_version_source_flow(self):
        d=self.study
        self.assertEqual((d["specimen_id"],d["version"]),("chatgpt-com",2))
        self.assertEqual({x["ref"] for x in d["source_resources"]},
                         {"R-JS-018","R-JS-069"})
        self.assertEqual(len(d["reviewed_stages"]),7)
        self.assertEqual(len(d["relationships"]),8)
        self.assertEqual(set(d["visible_control_roles"]),
                         {"previous_response","response_position_count","next_response"})
        self.assertFalse(d["source_executed"])
        self.assertFalse(d["live_selection_verified"])
        self.assertFalse(d["server_acknowledgement_verified"])
        self.assertTrue(d["caveats"])
        self.assertIn("rollback_and_cleanup",[x["id"] for x in d["reviewed_stages"]])

    def test_only_sanitized_semantic_summary_is_public(self):
        content=PATH.read_text("utf-8").lower()
        for restricted in ("https://","http://",".js","raw_source","authorization:",
                           "backend-api","requestbody","session_token","bearer ",
                           "page-snapshot", "source-dom","original_filename"):
            self.assertNotIn(restricted,content)

if __name__=="__main__":
    unittest.main()
