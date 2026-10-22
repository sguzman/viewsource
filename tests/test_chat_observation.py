"""No private data can fit in the strict chat observation vocabulary."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("validate_chat_observation",ROOT / "scripts/validate_chat_observation.py")
mod=importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)


class StructuralTraceTests(unittest.TestCase):
    def doc(self):
        return {
            "format_version":1,"feature_id":"chat-interaction",
            "experiment_type":"disposable_synthetic","evidence_status":"unreviewed",
            "privacy_boundary":"structural_counts_and_fixed_event_labels_only",
            "steps":[
                {"ordinal":0,"offset_ms":0,"event":"edit_draft","source":"synthetic_user_action",
                 "selection":"unknown","response_phase":"editing",
                 "message_count_delta":0,"conversation_count_delta":0,"parent_link_delta":0,"result":"observed"},
                {"ordinal":1,"offset_ms":130,"event":"submit_draft","source":"visible_ui_change",
                 "selection":"selected","response_phase":"sending",
                 "message_count_delta":1,"conversation_count_delta":1,"parent_link_delta":0,"result":"inconclusive"}
            ]}

    def test_valid_structure_is_not_verified(self):
        data=self.doc()
        self.assertEqual(mod.validate(data), [])
        self.assertEqual(data["evidence_status"],"unreviewed")

    def test_user_data_field_rejected(self):
        data=self.doc()
        data["steps"][0]["message_content"]="never publish"
        self.assertTrue(mod.validate(data))

    def test_account_identifier_field_rejected(self):
        data=self.doc()
        data["steps"][0]["conversation_id"]="synthetic-value"
        self.assertTrue(mod.validate(data))

    def test_unapproved_free_text_rejected(self):
        data=self.doc()
        data["steps"][1]["event"]="unrestricted text"
        self.assertTrue(mod.validate(data))

    def test_time_order_and_ordinal_checked(self):
        data=self.doc()
        data["steps"][1]["offset_ms"]=-1
        self.assertTrue(mod.validate(data))
        data=self.doc()
        data["steps"][1]["ordinal"]=99
        self.assertTrue(mod.validate(data))

    def test_numeric_bounds_and_boolean_rejected(self):
        data=self.doc()
        data["steps"][0]["message_count_delta"]=2000
        self.assertTrue(mod.validate(data))
        data=self.doc()
        data["steps"][0]["message_count_delta"]=True
        self.assertTrue(mod.validate(data))

    def test_non_disposable_input_not_accepted(self):
        data=self.doc()
        data["experiment_type"]="live_account"
        self.assertTrue(mod.validate(data))


if __name__=="__main__":
    unittest.main()
