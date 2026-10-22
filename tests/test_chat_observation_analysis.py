"""Strict candidate-event analysis without raw text or guessed verification."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "analyze_chat_observation", ROOT / "scripts/analyze_chat_observation.py")
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class ObservationAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = json.loads(
            (ROOT / "specimens/chatgpt-com/v0002/chat-interaction.graph.json")
            .read_text("utf-8"))

    @staticmethod
    def step(ordinal, offset, event, phase, result="observed", messages=0):
        return {
            "ordinal": ordinal, "offset_ms": offset, "event": event,
            "source": "synthetic_user_action", "selection": "unknown",
            "response_phase": phase, "message_count_delta": messages,
            "conversation_count_delta": 0, "parent_link_delta": 0,
            "result": result
        }

    def example(self):
        return {
            "format_version": 1, "feature_id": "chat-interaction",
            "experiment_type": "disposable_synthetic",
            "evidence_status": "unreviewed",
            "privacy_boundary": "structural_counts_and_fixed_event_labels_only",
            "steps": [
                self.step(0, 0, "edit_draft", "editing"),
                self.step(1, 25, "submit_draft", "sending", messages=1),
                self.step(2, 150, "response_started", "receiving"),
                self.step(3, 400, "response_completed", "complete", messages=1),
            ]
        }

    def test_structural_summary_not_runtime_proof(self):
        out = mod.summarize(self.example(), self.graph)
        self.assertEqual(out["step_count"], 4)
        self.assertEqual(out["duration_ms"], 400)
        self.assertEqual(out["structure_deltas"]["messages"], 2)
        self.assertEqual(out["verified_transition_count"], 0)
        self.assertFalse(out["transition_promotion_allowed"])
        self.assertEqual(out["result_counts"]["observed"], 4)

    def test_maps_possible_events_without_asserting_edges(self):
        out = mod.summarize(self.example(), self.graph)
        mapping = {x["event"]: x for x in out["candidate_event_correlations"]}
        self.assertEqual(mapping["submit_draft"]["candidate_transition_ids"], ["submit"])
        self.assertEqual(mapping["response_started"]["candidate_transition_ids"], ["receive"])
        self.assertEqual(mapping["submit_draft"]["mapping_status"], "candidate_only")

    def test_ambiguous_edit_event_remains_multiple_candidates(self):
        observation = self.example()
        observation["steps"] = [self.step(0, 0, "edit_message", "editing")]
        out = mod.summarize(observation, self.graph)
        item = out["candidate_event_correlations"][0]
        self.assertIn("start_message_edit", item["candidate_event_ids"])
        self.assertIn("submit_message_edit", item["candidate_event_ids"])
        self.assertGreater(len(item["candidate_transition_ids"]), 1)

    def test_unmapped_event_is_not_fabricated(self):
        observation = self.example()
        observation["steps"] = [self.step(0, 0, "other", "unknown", result="inconclusive")]
        out = mod.summarize(observation, self.graph)
        self.assertEqual(out["candidate_event_correlations"][0]["mapping_status"], "unmapped")
        self.assertEqual(out["verified_transition_count"], 0)

    def test_unapproved_content_and_identifiers_rejected(self):
        observation = self.example()
        observation["steps"][0]["message_text"] = "a private message"
        with self.assertRaises(mod.ObservationError):
            mod.summarize(observation, self.graph)
        observation = self.example()
        observation["steps"][0]["conversation_id"] = "forbidden"
        with self.assertRaises(mod.ObservationError):
            mod.summarize(observation, self.graph)

    def test_export_does_not_echo_structural_input_record(self):
        observation = self.example()
        out = mod.summarize(observation, self.graph)
        self.assertNotIn("steps", out)
        self.assertNotIn("offset_ms", json.dumps(out))
        self.assertTrue(all(item["mapping_status"] != "verified"
                            for item in out["candidate_event_correlations"]))


if __name__ == "__main__":
    unittest.main()
