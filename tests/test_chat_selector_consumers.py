"""Source-scoped selectors and UI consumption, excluding feature reference confusion."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"specimens/chatgpt-com/v0002/chat_selector_consumers.json"

class ChatSelectorConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(DATA.read_text("utf-8"))

    def test_selector_roles_and_ui_relationships(self):
        d=self.data
        self.assertEqual((d["specimen_id"],d["version"]),("chatgpt-com",2))
        self.assertFalse(d["source_executed"])
        self.assertFalse(d["ui_runtime_verified"])
        self.assertEqual(d["evidence_class"],"observed_static")
        selectors={s["id"]:s for s in d["selectors"]}
        self.assertEqual(len(selectors),5)
        self.assertEqual(len(d["verified_consumers"]),7)
        self.assertEqual(len(d["relationships"]),11)
        self.assertEqual(selectors["current_turn_path"]["kind"],"message_ancestry")
        self.assertEqual(selectors["full_selected_path"]["kind"],"message_ancestry")
        for name in ("automation_references","page_references"):
            self.assertEqual(selectors[name]["kind"],"feature_reference_state")
            self.assertIn("NOT visible transcript",selectors[name]["ui_meaning"])
        self.assertTrue(any(
            c["selector_id"]=="current_turn_path"
            and c["consumer_role"]=="conversation_answer_now_control"
            and c["kind"]=="react_scoped_selector_subscription"
            for c in d["verified_consumers"]
        ))
        for consumer in d["verified_consumers"]:
            self.assertIn(consumer["selector_id"],selectors)
            self.assertRegex(consumer["source_ref"],r"^R-JS-[0-9]{3}$")
        self.assertTrue(d["limitations"])

    def test_ui_click_actions_are_source_only_and_guarded(self):
        d=self.data
        item=d["reviewed_ui_action"]
        self.assertEqual(item["bound_selector"],"current_turn_path")
        self.assertEqual(item["source_ref"],"R-JS-018")
        self.assertFalse(item["live_click_observed"])
        self.assertEqual(set(item["rendered_surfaces"]),{
            "inline_button","escape_dialog_button"})
        self.assertEqual({x["name"] for x in item["paths"]},{
            "answer_now","skip_reasoning","error_recovery"})
        self.assertTrue(item["verification_boundary"])
        self.assertEqual(len(d["relationships"]),11)

    def test_no_capture_data_published(self):
        text=DATA.read_text("utf-8").lower()
        for forbidden in (
            "http://","https://",".js","source-dom","page-snapshot",
            "raw_source","backend-api","bearer ","authorization:",
            "session_token","original_filename","private_user"
        ):
            self.assertNotIn(forbidden,text)

if __name__=="__main__":
    unittest.main()
