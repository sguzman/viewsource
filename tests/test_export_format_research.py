"""Keep public export-format evidence separate from v0002 live-site claims."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "specimens/chatgpt-com/v0002"


class ExportFormatResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((BASE / "export_format_research.json").read_text("utf-8"))
        cls.record = json.loads((BASE / "record.json").read_text("utf-8"))

    def test_export_format_is_external_evidence(self):
        item = next(f for f in self.record["findings"] if f["id"] == "F2-070")
        evidence = item["evidence"]
        self.assertEqual(evidence["evidence_class"], "external_source")
        self.assertEqual(evidence["source_scope"], "public_reference")
        self.assertEqual(evidence["evidence_ref"], "E2-070")
        self.assertEqual(self.report["source_scope"], "public_reference")

    def test_tree_vocabulary_is_publicly_documented(self):
        fields = {entry["field"] for entry in self.report["export_tree_fields"]}
        self.assertEqual(fields, {"mapping","parent","children","current_node"})
        self.assertTrue(self.report["limitations"])
        self.assertEqual(self.report["local_tool"], "scripts/inspect_chat_export.py")
        self.assertTrue((ROOT / self.report["local_tool"]).is_file())

    def test_source_urls_are_known_public_refs(self):
        urls = [self.report["official"]["source_url"]]
        urls += [s["source_url"] for s in self.report["community"]]
        for url in urls:
            parsed = urlparse(url)
            self.assertEqual(parsed.scheme, "https")
            self.assertIn(parsed.hostname, {
                "help.openai.com", "github.com", "difegam.github.io"
            })

    def test_no_internal_chat_claim_or_private_samples(self):
        s = json.dumps(self.report)
        self.assertNotIn('"request_headers"', s)
        self.assertNotIn('"conversation_id"', s)
        self.assertNotIn('"message_text"', s)
        self.assertIn("not", self.report["limitations"][0].lower())


if __name__ == "__main__":
    unittest.main()
