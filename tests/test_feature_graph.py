"""Executable checks for typed library links and candidate chat state machines."""
from __future__ import annotations

from pathlib import Path
import json
import unittest
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.util.spec_from_file_location("viewsource_feature_validation", ROOT / "scripts" / "validate_feature_graph.py")
validation = importlib.util.module_from_spec(loader)
assert loader.loader is not None
loader.loader.exec_module(validation)


class FeatureGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = json.loads((ROOT / "specimens/chatgpt-com/v0002/technology_inventory.json").read_text("utf-8"))
        cls.graph = json.loads((ROOT / "specimens/chatgpt-com/v0002/chat-interaction.graph.json").read_text("utf-8"))
        cls.record = json.loads((ROOT / "specimens/chatgpt-com/v0002/record.json").read_text("utf-8"))

    def test_feature_graph_validate(self):
        errors = []
        validation.validate_extensions(lambda passed, text: errors.append(text) if not passed else None, "chatgpt-com", 2)
        self.assertEqual(errors, [])

    def test_typed_technology_node_links(self):
        nodes = {c["id"]: c for c in self.record["components"]}
        self.assertEqual(len(self.inventory["technologies"]), 11)
        for item in self.inventory["technologies"]:
            node = nodes[item["component_ref"]]
            self.assertEqual(node["kind"], "Dependency")
            self.assertEqual(node["properties"]["detection_strength"], item["confidence"])
            self.assertEqual(node["properties"]["proposed_role"], item["role"])
            self.assertFalse(node["properties"]["version_established"])
        for link in self.graph["technology_links"]:
            self.assertIn(link["component_ref"], nodes)
            self.assertFalse(link["feature_ownership_verified"])

    def test_state_machines_link_events_and_are_unverified(self):
        graph=self.graph
        self.assertEqual(graph["model_status"], "candidate")
        self.assertEqual({m["id"] for m in graph["machines"]}, {"selection","response"})
        self.assertEqual(len(graph["transitions"]),14)
        self.assertEqual(len(graph["surfaces"]),6)
        self.assertTrue(all(t["evidence_status"]=="hypothesis" and t["evidence_refs"]==[]
                            and t["verify"] for t in graph["transitions"]))
        event_ids={e["id"] for e in graph["events"]}
        for machine in graph["machines"]:
            state_ids={s["id"] for s in machine["states"]}
            self.assertIn(machine["initial_state"],state_ids)
            for transition in [t for t in graph["transitions"] if t["machine"]==machine["id"]]:
                self.assertIn(transition["event"],event_ids)
                self.assertIn(transition["from"],state_ids)
                self.assertIn(transition["to"],state_ids)

    def test_structural_evidence_not_relabelled_as_live(self):
        self.assertEqual(self.graph["source_scope"], "saved_archive")
        self.assertTrue(all(surface["basis"]=="observed_static" for surface in self.graph["surfaces"]))
        self.assertEqual(self.graph["branch_model"]["status"], "not_established")
        self.assertGreaterEqual(len(self.graph["open_questions"]),5)

    def test_graph_contains_no_capture_data(self):
        text=json.dumps(self.graph)
        self.assertNotRegex(text, r"https?://")
        self.assertNotRegex(text, r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}")
        self.assertNotRegex(text, r"user-[A-Za-z0-9]{4,}")
        for field in ("raw_html","source_excerpt","chat_text","session_token","capture_url","request_headers"):
            self.assertNotIn('"' + field + '"', text)


if __name__ == "__main__":
    unittest.main()
