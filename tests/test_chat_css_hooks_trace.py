"""Verify the saved CSS style-hook census is bounded and does not infer DOM binding."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"specimens/chatgpt-com/v0002/chat_css_hooks_trace.json"
class CssHookEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(SOURCE.read_text("utf8"))
    def test_counts_and_limits(self):
        d=self.data
        self.assertEqual((d["specimen_id"],d["version"]),("chatgpt-com",2))
        self.assertEqual(d["stylesheets_scanned"],17)
        self.assertEqual(d["javascript_bundles_scanned"],144)
        self.assertEqual(d["css_bytes"],2340628)
        self.assertEqual(d["css_lexical_occurrences"]["media_at_rules"],627)
        self.assertEqual(d["css_lexical_occurrences"]["container_at_rules"],504)
        self.assertEqual(d["css_lexical_occurrences"]["focus_visible_pseudo_classes"],493)
        self.assertTrue(all(v==0 for v in d["exact_css_attribute_selector_absence"].values()))
        self.assertEqual(d["cross_resource_vocabulary"]["thread_content"]["javascript_bundle_count"],11)
        self.assertTrue(d["not_verified"])
        self.assertEqual(d["evidence_class"],"observed_static_syntax")
    def test_no_captured_asset_material(self):
        text=SOURCE.read_text("utf8").lower()
        for bad in ("https://","http://","raw_source",".css","page-snapshot",
                    "session_token","authorization:","source-dom",
                    "original_filename","private_message"):
            self.assertNotIn(bad,text)
if __name__=="__main__":
    unittest.main()
