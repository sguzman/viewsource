"""Publication guard accepts common public prose and blocks secret-shaped strings.

Synthetic examples are assembled in memory, never stored as real identifiers.
The scan reports only a file path, not any matched value.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "publication_guard", ROOT / "scripts/publication_guard.py")
guard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = guard
spec.loader.exec_module(guard)


class PublicationGuardTests(unittest.TestCase):
    def test_account_id_shapes_are_detected(self):
        self.assertTrue(guard.contains_sensitive_shape("user-" + "q" * 22))
        self.assertTrue(guard.contains_sensitive_shape("org-" + "w" * 18))
        self.assertFalse(guard.contains_sensitive_shape("user-" + "x" * 4))

    def test_credential_shaped_urls_are_detected(self):
        self.assertTrue(guard.contains_sensitive_shape(
            "https://sample.invalid/view?access_token=" + "x" * 24))
        self.assertTrue(guard.contains_sensitive_shape(
            "https://sample.invalid/view?api_key=" + "z" * 20))
        self.assertFalse(guard.contains_sensitive_shape(
            "https://help.openai.com/en/articles/6825453-chatgpt-release-notes"))

    def test_bearer_and_compact_tokens_are_detected(self):
        self.assertTrue(guard.contains_sensitive_shape(
            "Authorization: Bearer " + "a" * 36))
        self.assertTrue(guard.contains_sensitive_shape(
            "eyJ" + "a" * 22 + "." + "b" * 25 + "." + "c" * 20))

    def test_no_raw_values_in_report(self):
        self.assertIsInstance(guard.scan(), list)
        self.assertEqual(guard.scan(), [])


if __name__ == "__main__":
    unittest.main()
