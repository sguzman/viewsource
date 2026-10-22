"""Candidate-only state exploration never turns a synthetic path into proof."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("simulate_chat_scenario",
                                             ROOT / "scripts/simulate_chat_scenario.py")
sim = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = sim
spec.loader.exec_module(sim)


class ChatScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = json.loads(
            (ROOT / "specimens/chatgpt-com/v0002/chat-interaction.graph.json")
            .read_text("utf-8"))

    @staticmethod
    def scenario(*steps):
        return {"format_version": 1,
                "steps": [{"machine": machine, "event": event} for machine, event in steps]}

    def test_complete_hypothetical_response_lifecycle(self):
        sequence = self.scenario(
            ("response", "edit_draft"), ("response", "submit_draft"),
            ("response", "response_started"), ("response", "response_completed"))
        result = sim.simulate(self.graph, sequence, assume_guards=True)
        self.assertEqual(result["machine_states"]["response"], "complete")
        self.assertEqual(result["machine_states"]["selection"], "none")
        self.assertEqual(len(result["trace"]), 4)
        self.assertFalse(result["verified_runtime_behavior"])
        self.assertFalse(result["performed_site_actions"])
        self.assertTrue(all(t["evidence_status"] == "hypothetical_simulation"
                            for t in result["trace"]))
        self.assertTrue(result["trace"][1]["assumed_guards"])

    def test_guard_not_silently_accepted(self):
        case = self.scenario(("response", "edit_draft"),
                             ("response", "submit_draft"))
        with self.assertRaisesRegex(sim.ScenarioError,"Guard assumptions required"):
            sim.simulate(self.graph, case)

    def test_no_auto_transition_on_unknown_event(self):
        case = self.scenario(("response", "response_completed"))
        with self.assertRaisesRegex(sim.ScenarioError,"No unique candidate"):
            sim.simulate(self.graph, case)
        with self.assertRaises(sim.ScenarioError):
            sim.simulate(self.graph, self.scenario(("response", "unknown")))

    def test_independent_machine_state(self):
        case = self.scenario(("selection","select_conversation"),
                             ("response","edit_draft"),
                             ("selection","select_conversation"))
        result = sim.simulate(self.graph, case)
        self.assertEqual(result["machine_states"]["selection"], "selected")
        self.assertEqual(result["machine_states"]["response"], "editing")
        self.assertEqual(result["machine_states"]["message_operation"], "viewing")

    def test_extra_fields_cannot_carry_private_payload(self):
        case = self.scenario(("response","edit_draft"))
        case["steps"][0]["content"] = "not allowed"
        with self.assertRaisesRegex(sim.ScenarioError,"extra fields"):
            sim.simulate(self.graph, case)
        case = self.scenario(("response","edit_draft"))
        case["conversation_key"] = "not allowed"
        with self.assertRaises(sim.ScenarioError):
            sim.simulate(self.graph, case)

    def test_duplicate_machine_transition_is_rejected(self):
        import copy
        altered = copy.deepcopy(self.graph)
        original = next(t for t in altered["transitions"] if t["id"] == "begin_edit")
        duplicate = {**original,"id":"synthetic-duplicate"}
        altered["transitions"].append(duplicate)
        with self.assertRaisesRegex(sim.ScenarioError,"No unique candidate"):
            sim.simulate(altered,self.scenario(("response","edit_draft")))

    def test_empty_scenario_keeps_initial_states(self):
        result=sim.simulate(self.graph,self.scenario())
        self.assertEqual(result["trace"],[])
        self.assertEqual(result["machine_states"]["response"],"idle")


if __name__=="__main__":
    unittest.main()
