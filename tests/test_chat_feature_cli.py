"""Evidence-graded feature graph reader tests: never execute site actions."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("chat_feature_cli",ROOT / "scripts/chat_feature_cli.py")
module=importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name]=module
spec.loader.exec_module(module)


class FeatureConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model=module.FeatureGraphModel.from_file()

    def test_query_candidate_submissions(self):
        rows=self.model.query("response",from_state="editing",event="submit_draft")
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["to"],"sending")
        self.assertEqual(rows[0]["evidence_status"],"hypothesis")

    def test_query_machine_scoping(self):
        selection=self.model.query("selection")
        response=self.model.query("response")
        self.assertEqual(len(selection),3)
        self.assertEqual(len(response),11)
        self.assertTrue(all(t["machine"]=="selection" for t in selection))
        self.assertTrue(all(t["machine"]=="response" for t in response))

    def test_verification_gate_closed(self):
        with self.assertRaisesRegex(module.FeatureGraphError,"no independent live verification"):
            self.model.resolve_verified("response","editing","submit_draft")
        with self.assertRaisesRegex(module.FeatureGraphError,"absent or ambiguous"):
            self.model.resolve_verified("response","editing","stop_response")

    def test_dot_is_dashed_for_hypotheses(self):
        dot=self.model.to_dot("response")
        self.assertIn("digraph feature",dot)
        self.assertIn("style=dashed",dot)
        self.assertNotIn("style=solid",dot)
        self.assertIn('"editing" -> "sending"',dot)

    def test_domain_graph_remains_hypothetical(self):
        graph=self.model.graph
        self.assertEqual(len(self.model.domain_relations),8)
        self.assertTrue(all(e["evidence_status"]=="hypothesis" for e in self.model.domain_relations))
        self.assertTrue(all(e["verified_evidence_refs"]==[] for e in self.model.domain_relations))
        dot=self.model.to_domain_dot()
        self.assertIn("digraph domain",dot)
        self.assertIn('"message" -> "message"',dot)
        self.assertIn("style=dashed",dot)
        self.assertNotIn("style=solid",dot)
        self.assertIn("\\n",dot)

    def test_domain_relation_rejects_bad_entity(self):
        import copy
        data=copy.deepcopy(self.model.graph)
        data["domain_relations"][0]["to"]="missing"
        with self.assertRaises(module.FeatureGraphError):
            module.FeatureGraphModel(data)

    def test_reject_unknown_references(self):
        with self.assertRaises(module.FeatureGraphError):
            self.model.query("missing")
        with self.assertRaises(module.FeatureGraphError):
            self.model.query("response",from_state="unknown")
        with self.assertRaises(module.FeatureGraphError):
            self.model.query("response",event="unknown")
        with self.assertRaises(module.FeatureGraphError):
            self.model.to_dot("missing")

    def test_invalid_graph_references_not_accepted(self):
        invalid={"machines":[{"id":"m","states":[{"id":"one"}],"initial_state":"one"}],
                 "events":[{"id":"a"}],"transitions":[{"id":"t","machine":"m","from":"one",
                "to":"unknown","event":"a","evidence_status":"hypothesis"}]}
        with self.assertRaises(module.FeatureGraphError):
            module.FeatureGraphModel(invalid)


if __name__=="__main__":
    unittest.main()
