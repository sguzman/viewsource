"""Saved client conversation collection storage and query-cache provenance."""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/"specimens/chatgpt-com/v0002/chat_persistence_cache_trace.json"

class ChatClientCacheTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.study=json.loads(FILE.read_text(encoding="utf8"))

    def test_versioned_cache_and_query_cache_are_distinct(self):
        d=self.study
        self.assertEqual((d["specimen_id"],d["version"]),("chatgpt-com",2))
        self.assertEqual([(x["ref"],x["module_ordinal"]) for x in d["source_resources"]],
                         [("R-JS-018",473),("R-JS-018",81)])
        self.assertEqual(d["evidence_class"],"observed_static")
        self.assertEqual(len(d["stages"]),9)
        self.assertEqual(len(d["source_relationships"]),9)
        for field in ("executed_in_browser","local_storage_write_verified",
                      "server_durability_verified","cross_tab_behavior_verified"):
            self.assertFalse(d[field])
        self.assertTrue(any("metadata caching" in x["description"]
                            for x in d["stages"]))
        self.assertTrue(d["still_unverified"])
        self.assertEqual(d["cross_tab_boundary"]["evidence_class"], "source_reviewed_limit")
        self.assertFalse(d["cross_tab_behavior_verified"])

    def test_private_storage_identifiers_are_not_published(self):
        s=FILE.read_text("utf8").lower()
        for forbidden in ("http://","https://",".js","source-dom","page-snapshot",
                          "raw_source","authorization:","bearer ",
                          "session_token","original_storage_key","storage_value"):
            self.assertNotIn(forbidden,s)

if __name__=="__main__":
    unittest.main()
