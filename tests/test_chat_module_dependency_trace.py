"""Reproduced anonymous module import census with explicit static-only limits."""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/"specimens/chatgpt-com/v0002/chat_module_dependency_trace.json"

class ModuleDependencyTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(FILE.read_text("utf8"))

    def test_counts_and_curated_edges(self):
        d=self.data
        self.assertEqual((d["specimen_id"],d["version"]),("chatgpt-com",2))
        c=d["census"]
        self.assertEqual(c["parsed_bundles"],144)
        self.assertEqual(c["parse_failures"],0)
        self.assertEqual(c["module_registry_entries"],10399)
        self.assertEqual(c["distinct_literal_import_candidates"],51285)
        self.assertEqual(c["uniquely_resolved_import_candidates"]+
                         c["ambiguous_import_candidates"]+
                         c["unresolved_import_candidates"],
                         c["distinct_literal_import_candidates"])
        self.assertEqual(c["cross_bundle_resolved_candidates"]+
                         c["same_bundle_resolved_candidates"],
                         c["uniquely_resolved_import_candidates"])
        self.assertFalse(d["live_module_load_verified"])
        self.assertFalse(d["server_behavior_verified"])
        self.assertFalse(d["source_assets_published"])
        edges=d["curated_verified_syntax_edges"]
        self.assertEqual(len(edges),4)
        self.assertEqual(len({(e["from_ref"],e["from_module"],
                              e["to_ref"],e["to_module"]) for e in edges}),4)
        self.assertTrue(all(x["evidence_class"]=="observed_static_syntax"
                            for x in edges))
        self.assertTrue(d["limits"])
        shape=d["reviewed_export_shape_matches"]
        self.assertEqual(len(shape),1)
        item=shape[0]
        self.assertEqual((item["from_ref"],item["to_ref"]),("R-JS-018","R-JS-004"))
        self.assertEqual((item["registry_candidate_count"],item["compatible_interface_count"]),(2,1))
        self.assertEqual(len(item["required_export_roles"]),3)
        self.assertFalse(item["runtime_import_verified"])

    def test_private_identifiers_are_not_published(self):
        text=FILE.read_text("utf8").lower()
        for forbidden in ("https://","http://",".js","raw_source",
                          "authorization:","bearer ","original_filename",
                          "source-dom","page-snapshot","session_token",
                          "module_key=", "request_body="):
            self.assertNotIn(forbidden,text)

if __name__=="__main__":
    unittest.main()
