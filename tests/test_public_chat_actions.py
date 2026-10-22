"""Documented user controls are not secretly promoted to verified source behavior."""
from __future__ import annotations

import json
from pathlib import Path
import unittest
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


class PublicChatActionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = ROOT / "specimens/chatgpt-com/v0002"
        cls.actions = json.loads((base / "public_chat_actions.json").read_text("utf-8"))
        cls.graph = json.loads((base / "chat-interaction.graph.json").read_text("utf-8"))

    def test_documented_actions_are_not_runtime_evidence(self):
        self.assertEqual(self.actions["scope"], "official_public_documentation")
        self.assertEqual(len(self.actions["actions"]), 4)
        self.assertEqual({a["status"] for a in self.actions["actions"]}, {"documented_ui"})
        self.assertTrue(all(a["unknown"] for a in self.actions["actions"]))
        self.assertEqual({t["evidence_status"] for t in self.graph["transitions"]}, {"hypothesis"})

    def test_sources_are_public_and_graph_events_are_real_candidates(self):
        known = {e["id"] for e in self.graph["events"]}
        for action in self.actions["actions"]:
            url = urlparse(action["source_url"])
            self.assertEqual(url.scheme, "https")
            self.assertEqual(url.netloc, "help.openai.com")
            self.assertTrue(url.path.startswith("/en/articles/"))
            self.assertTrue(set(action["graph_events"]) <= known)
            self.assertIn(action["capture_ref"], {None, "E2-069"})
            self.assertTrue(action["summary"] and action["source_title"])

    def test_no_private_values_or_website_protocol_examples(self):
        text = json.dumps(self.actions)
        for marker in ("session_cookie", "message_content", "account_identifier",
                       "request_payload", "authorization_header"):
            self.assertNotIn(marker, text)


if __name__ == "__main__":
    unittest.main()
