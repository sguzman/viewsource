"""Static-only transcript windowing and scroll preservation evidence."""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/"specimens/chatgpt-com/v0002/chat_viewport_virtualization_trace.json"

class ViewportTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads(DOC.read_text(encoding="utf-8"))

    def test_verified_source_scope(self):
        d=self.d
        self.assertEqual((d["specimen_id"],d["version"]),("chatgpt-com",2))
        self.assertEqual(d["evidence_class"],"observed_static")
        self.assertFalse(d["runtime_viewport_verified"])
        self.assertFalse(d["server_scrolling_contract_verified"])
        self.assertEqual({x["ref"] for x in d["source_resources"]},
                         {"R-JS-066","R-JS-069","R-JS-072"})
        self.assertEqual(len(d["source_chain"]),7)
        self.assertEqual(len(d["windowing_rules"]),11)
        self.assertEqual(len(d["static_relationships"]),3)
        self.assertEqual(
            {(x["source_ref"],x["module_ordinal"]) for x in d["module_anchors"]},
            {("R-JS-066",9),("R-JS-066",14),("R-JS-072",13),("R-JS-072",14)}
        )
        self.assertTrue(d["module_ordinal_contract"])
        reconciliation=d["selected_branch_window_reconciliation"]
        self.assertEqual([x["source_ref"] for x in reconciliation["stages"]],
                         ["R-JS-018","R-JS-072","R-JS-066","R-JS-066"])
        self.assertFalse(reconciliation["runtime_effect_verified"])
        self.assertEqual(len(reconciliation["limits"]),3)
        spacer=d["composer_spacer_wiring"]
        self.assertFalse(spacer["live_scroll_verified"])
        self.assertEqual(len(spacer["stages"]),4)
        self.assertEqual([s["source_ref"] for s in spacer["stages"]],
                         ["R-JS-072","R-JS-072","R-JS-072","R-JS-066"])
        self.assertEqual(len(spacer["boundaries"]),3)
        ast=d["ast_candidate_recheck"]
        self.assertFalse(ast["verified_runtime"])
        self.assertFalse(ast["module_ownership_by_ast_only"])
        self.assertEqual(
            [(x["source_ref"],x["module_ordinal"],len(x["patterns"]))
             for x in ast["module_matches"]],
            [("R-JS-066",9,7),("R-JS-066",14,1),
             ("R-JS-072",13,1),("R-JS-072",14,2)]
        )
        self.assertTrue(ast["limitation"])
        self.assertTrue(d["still_unverified"])
        ids=[row["id"] for row in d["windowing_rules"]]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertTrue({"viewport_binary_search","scroll_anchor_compensation",
                         "retained_offscreen_turns","voice_spacer_positioning",
                         "user_input_cancellation"}<=set(ids))
        for row in d["windowing_rules"]:
            self.assertTrue(row["limits"])
            self.assertIn(row["ref"],{"R-JS-066","R-JS-072"})
        for edge in d["source_chain"]:
            self.assertRegex(edge["ref"],r"^R-JS-[0-9]{3}$")

    def test_report_excludes_private_captured_assets(self):
        text=DOC.read_text(encoding="utf-8").lower()
        for invalid in ("https://","http://",".js","bundle-","source-dom",
                        "page-snapshot","bearer ","authorization:",
                        "account_id","session_token","raw_source",
                        "original_filename","cookies"):
            self.assertNotIn(invalid,text)

if __name__=="__main__":
    unittest.main()
