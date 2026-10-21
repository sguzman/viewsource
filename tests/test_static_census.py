"""Privacy isolation and census regression tests using synthetic sources only."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("static_census", REPO / "scripts/static_census.py")
import sys
sys.path.insert(0, str(REPO / "scripts"))
census = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(census)


class StaticCensusTests(unittest.TestCase):
    SECRET = "VERY_PRIVATE_TEST_SENTINEL_DO_NOT_PUBLISH"
    def test_html_counts_and_secret_not_in_report(self):
        html = ("""<!doctype html><html data-theme-user-id="PRIVATE"><head>
        <link rel="stylesheet" href="private-bundle.css">
        <style>@media (prefers-reduced-motion: reduce) {} :root {--accent: #fff}</style>
        <script type="application/json">{"conversation":"VERY_PRIVATE_TEST_SENTINEL_DO_NOT_PUBLISH"}</script>
        <script>window.__reactRouterContext.streamController.enqueue("PRIVATE");
        sessionStorage.getItem("private");</script></head><body>
        <nav aria-label="PRIVATE"><button data-state="closed" aria-expanded="false">PRIVATE</button></nav>
        <form><input type="file" multiple></form><img src="private-image"><svg></svg>
        </body></html>""").encode()
        result = census.scan_html(html)
        self.assertEqual(result["tag_counts"]["button"], 1)
        self.assertEqual(result["attribute_counts"]["aria-label"], 1)
        self.assertEqual(result["resource_and_script_counts"]["inline_json_script"], 1)
        self.assertEqual(result["resource_and_script_counts"]["external_stylesheet"], 1)
        self.assertEqual(result["resource_and_script_counts"]["file_input"], 1)
        self.assertEqual(result["resource_and_script_counts"]["react_router_stream_script"], 1)
        self.assertTrue(result["presence_flags"]["account_linked_attribute_present"])
        self.assertNotIn(self.SECRET, str(result))
        self.assertNotIn("private-image", str(result))
        self.assertNotIn("PRIVATE", str(result))

    def test_html_copy_and_zip_sanitization(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            html = root / "private.html"
            html.write_text("<main><a href='private-url'>secret</a></main>")
            standalone = census.scan_capture(html)
            self.assertEqual(standalone["pages_inspected"], 1)
            self.assertEqual(standalone["capture_scope"], "saved_page")
            self.assertNotIn("private-url", str(standalone))
            z = root / "input.zip"
            with zipfile.ZipFile(z, "w") as archive:
                archive.writestr("private/index.html", html.read_bytes())
                archive.writestr("private/asset.js", "SECRET")
            archived = census.scan_capture(z)
            self.assertEqual(archived["pages_inspected"], 1)
            self.assertEqual(archived["capture_scope"], "saved_archive")
            self.assertEqual(archived["tag_counts"]["main"], 1)

    def test_zip_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            z = Path(temp) / "bad.zip"
            with zipfile.ZipFile(z, "w") as archive:
                archive.writestr("../outside.html", "unsafe")
            with self.assertRaisesRegex(ValueError, "Unsafe archive"):
                census.scan_capture(z)


if __name__ == "__main__":
    unittest.main()
