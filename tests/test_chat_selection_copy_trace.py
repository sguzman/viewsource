"""Source-limited selection popover and code-copy evidence."""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"specimens/chatgpt-com/v0002/chat_selection_copy_trace.json"

class SelectionCopyTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.study=json.loads(SOURCE.read_text(encoding="utf-8"))

    def test_paths_and_verified_scope(self):
        d=self.study
        self.assertEqual((d["specimen_id"],d["version"]),("chatgpt-com",2))
        self.assertEqual(d["source_refs"],["R-JS-072"])
        self.assertEqual(d["evidence_class"],"observed_static")
        self.assertFalse(d["runtime_interaction_verified"])
        self.assertFalse(d["clipboard_write_verified"])
        self.assertFalse(d["server_behavior_verified"])
        self.assertEqual(len(d["selected_text"]["stages"]),6)
        self.assertEqual(len(d["last_code_block_copy"]["stages"]),7)
        self.assertEqual(len(d["cross_feature_relationships"]),4)
        self.assertTrue(any("writing blocks" in row["operation"]
                            for row in d["selected_text"]["stages"]))
        self.assertTrue(any("AbortController" in row["operation"]
                            for row in d["last_code_block_copy"]["stages"]))
        self.assertTrue(d["unverified"])

    def test_publication_has_no_archive_or_captured_private_data(self):
        text=SOURCE.read_text(encoding="utf-8").lower()
        for forbidden in ("https://","http://","authorization:",".js",
                          "source-dom","page-snapshot","raw_source","bundle-",
                          "session_token","original_filename","copy_payload",
                          "bearer "):
            self.assertNotIn(forbidden,text)

if __name__=="__main__":
    unittest.main()
