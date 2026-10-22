"""The published atlas must contain only curated research and renderable assets."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("viewsource_site_builder", ROOT / "scripts/build_site.py")
builder = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(builder)


class AtlasTests(unittest.TestCase):
    def test_atlas_build_and_chapters(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "atlas"
            result = builder.build(dest)
            self.assertEqual(len(result["specimens"]), 1)
            self.assertEqual(len(result["versions"]), 2)
            self.assertTrue((dest / "index.html").exists())
            self.assertTrue((dest / "app.css").exists())
            self.assertTrue((dest / "app.js").exists())
            self.assertTrue((dest / "explorer.js").exists())
            self.assertTrue((dest / "chat-graph.js").exists())
            self.assertTrue((dest / ".nojekyll").exists())
            data = json.loads((dest / "data/catalog.json").read_text(encoding="utf-8"))
            current = next(v for v in data["versions"] if v["version"] == 2)
            self.assertEqual(len(current["chapters"]), 14)
            self.assertEqual(len(current["visuals"]["technology"]["technologies"]), 11)
            self.assertEqual(len(current["visuals"]["page_map"]["nodes"]), 7)
            feature = current["visuals"]["feature_graph"]
            self.assertEqual(len(feature["machines"]), 2)
            self.assertEqual(len(feature["transitions"]), 14)
            self.assertEqual(len(feature["surfaces"]), 6)
            self.assertEqual(current["visuals"]["chat_source_signals"]["summary"][0]["count"], 63)
            self.assertEqual(len(current["visuals"]["feature_research"]["tasks"]), 17)

            self.assertTrue(all(t["evidence_status"] == "hypothesis" for t in feature["transitions"]))
            self.assertTrue((dest / feature["json_path"]).exists())
            self.assertEqual(json.loads((dest / feature["json_path"]).read_text(encoding="utf-8")), feature)

            self.assertEqual(current["visuals"]["module_imports"]["static_edges"], 236)
            self.assertEqual(len(current["visuals"]["module_imports"]["sources"]), 8)
            self.assertEqual(current["visuals"]["icons"]["matched_uses"], 92)
            self.assertEqual(current["visuals"]["css_system"]["distinct_tokens"], 2509)
            self.assertEqual(current["visuals"]["source_system"]["lexical_scopes"]["fetch_and_stream"], 5)
            self.assertEqual(len(current["visuals"]["source_system"]["event_signals"]), 6)
            self.assertEqual(len(current["visuals"]["source_system"]["state_signals"]), 7)
            self.assertEqual(len(current["visuals"]["source_system"]["network_signals"]), 6)
            self.assertEqual(len(current["visuals"]["css_system"]["token_groups"]), 8)
            self.assertEqual(current["visuals"]["landmarks"]["button_total"], 130)
            self.assertEqual(next(v for v in data["versions"] if v["version"] == 1)["visuals"], {})
            self.assertEqual(len(current["findings"]), 69)
            self.assertEqual(len(current["tasks"]), 91)
            self.assertGreaterEqual(len(current["components"]), 270)
            self.assertEqual(current["status"], "reviewed")
            self.assertEqual(len([t for t in current["tasks"] if "-followup-deep-" in t["id"]]), 57)
            previous = next(v for v in data["versions"] if v["version"] == 1)
            self.assertEqual(previous["status"], "reviewed")
            self.assertEqual(previous["chapters"], [])
            serialized = (dest / "data/catalog.json").read_text(encoding="utf-8").lower()
            for token in ("page-snapshot-chatgpt.com", "source-dom.html", "session_token",
                          "SYNTHETIC_PRIVATE_EMAIL_SENTINEL", "SYNTHETIC_PRIVATE_USER_SENTINEL"):
                self.assertNotIn(token, serialized)

    def test_appearance_controls_and_no_external_framework(self):
        html = (ROOT / "site/index.html").read_text(encoding="utf-8")
        js = (ROOT / "site/app.js").read_text(encoding="utf-8")
        css = (ROOT / "site/app.css").read_text(encoding="utf-8")
        for mode in ("system", "light", "dark"):
            self.assertIn('value="' + mode + '"', html)
        self.assertIn('data-theme="system"', html)
        self.assertIn('prefers-color-scheme: dark', css)
        self.assertIn('viewsource:theme', js)
        self.assertIn('document.createElement', js)
        self.assertNotIn("innerHTML", js)
        self.assertIn('data/catalog.json', js)


if __name__ == "__main__":
    unittest.main()
