"""Evidence limitations and invariants for the captured graph-mutation study."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"specimens/chatgpt-com/v0002/chat_graph_mutation_trace.json"

class StaticGraphMutationStudy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.item=json.loads(PATH.read_text(encoding="utf-8"))

    def test_source_scoping_and_graph_roles(self):
        d=self.item
        self.assertEqual((d["specimen_id"],d["version"]),("chatgpt-com",2))
        self.assertEqual(d["source_ref"],"R-JS-018")
        self.assertEqual(d["evidence_class"],"observed_static")
        self.assertFalse(d["captured_client_executed"])
        self.assertFalse(d["backend_schema_verified"])
        self.assertFalse(d["live_graph_behavior_verified"])
        self.assertEqual(len(d["source_modules"]),4)
        self.assertEqual(len(d["verified_source_call_sequence"]),9)
        self.assertEqual(len(d["graph_operations"]),11)
        self.assertTrue(d["not_verified"])
        projections=d["state_commit_observation"]["projected_state_roles"]
        self.assertIn("visible_selected_path_messages",projections)
        self.assertIn("selected_user_message_ancestry",projections)
        self.assertEqual(d["state_commit_observation"]["evidence_class"],"observed_static")
        self.assertEqual(set(d["mapping_transformer_results"]),{
            "updated_mapping","message_identity","is_new_node","did_rotate_descendant"
        })
        self.assertIn("selected_node_decision",
                      [step["kind"] for step in d["graph_operations"]])

    def test_no_private_input_or_source_snippet(self):
        content=PATH.read_text("utf-8").lower()
        for forbidden in (
            "https://","http://",".js","bundle-","page-snapshot",
            "source-dom","session_token","authorization:","bearer ",
            "raw_source","original_filename","conversation_id=",
            "account_id=","client_secret"
        ):
            self.assertNotIn(forbidden,content)

if __name__=="__main__":
    unittest.main()
