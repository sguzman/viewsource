"""Regression checks for offline Viewsource intake and task-graph generation."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("viewsource_tool", REPO / "scripts/viewsource.py")
tool = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(tool)

spec_validate = importlib.util.spec_from_file_location("viewsource_validate", REPO / "scripts/validate.py")
validator = importlib.util.module_from_spec(spec_validate)
assert spec_validate.loader is not None
spec_validate.loader.exec_module(validator)


class OfflineIntakeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.root = self.base / "public_repo"
        (self.root / "specimens").mkdir(parents=True)
        (self.root / "queues").mkdir()
        (self.root / "gallery").mkdir()
        (self.root / "ontology").mkdir()
        (self.root / "schemas").mkdir()
        self.original_root = tool.ROOT
        self.original_work = tool.WORKDIR
        self.original_validate_root = validator.ROOT
        tool.ROOT = self.root
        tool.WORKDIR = self.root / ".work"
        validator.ROOT = self.root
        for resource in ("queues/profiles.json", "queues/deep_profiles.json", "queues/static_profiles.json", "ontology/ontology.json",
                         "tarium.json", "gallery/index.json"):
            source = REPO / resource
            target = self.root / resource
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
        for resource, data in (
            ("specimens/index.json", {"format_version": 1, "specimens": []}),
            ("queues/tasks.json", {"format_version": 1, "tasks": []}),
            ("gallery/index.json", {"format_version": 1, "entries": []}),
        ):
            tool.save_json(self.root / resource, data)
        for resource in ("ontology/README.md", "gallery/README.md"):
            (self.root / resource).write_text("Public project resource\n", encoding="utf-8")

    def tearDown(self) -> None:
        tool.ROOT = self.original_root
        tool.WORKDIR = self.original_work
        validator.ROOT = self.original_validate_root
        self.temporary.cleanup()

    def example_zip(self, name="capture.zip", unsafe=False) -> Path:
        source = self.base / name
        with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as archive:
            if unsafe:
                archive.writestr("../outside.html", "<html>unsafe</html>")
            else:
                archive.writestr("index.html", """<!doctype html><html><head>
                <link rel="stylesheet" href="styles.css"><script defer src="site.js"></script>
                </head><body><main><form action="/save"><button>Submit</button></form>
                <img src="logo.png"></main></body></html>""")
                archive.writestr("site.js", "const x = fetch('/api/list'); localStorage.getItem('x')")
                archive.writestr("styles.css", "@font-face {} @media (width < 700px) { :root {--space: 1rem}}")
                archive.writestr("logo.png", b"\x89PNG\r\n")
        return source

    def test_queue_process_and_refresh(self) -> None:
        tool.queue_specimen("example", "https://example.org")
        with self.assertRaisesRegex(ValueError, "already exists"):
            tool.queue_specimen("example", "https://example.org")
        source = self.example_zip()
        self.assertEqual(tool.process_specimen("example", source), 1)
        private = tool.load_json(self.root / ".work/example/v0001/inventory.json")
        self.assertEqual(private["categories"], {"html": 1, "image": 1, "script": 1, "stylesheet": 1})
        self.assertEqual(private["files"][0]["observations"]["scripts"][0]["src"], "site.js")
        self.assertEqual(private["files"][1]["observations"]["fetch_references"], 1)
        tasks = tool.load_json(self.root / "queues/tasks.json")["tasks"]
        self.assertGreater(len(tasks), len(tool.load_json(self.root / "queues/profiles.json")["profiles"]))
        source_tasks = [t for t in tasks if "-followup-static-" in t["id"]]
        self.assertTrue(source_tasks)
        self.assertTrue(all("Static implementation trace:" in t["notes"] for t in source_tasks))
        self.assertTrue(all(t["status"] == "queued" for t in tasks))
        record = tool.load_json(self.root / "specimens/example/v0001/record.json")
        self.assertEqual(record["components"], [])
        self.assertFalse((self.root / "specimens/example/v0001/index.html").exists())
        self.assertFalse((self.root / "specimens/example/v0001/capture.zip").exists())
        self.assertEqual(tool.process_specimen("example", source), 2)
        index = tool.load_json(self.root / "specimens/index.json")["specimens"][0]
        self.assertEqual(index["versions"], [1, 2])
        self.assertTrue((self.root / "specimens/example/v0001/record.json").exists())
        self.assertEqual(validator.validate(), [])

    def test_requeue_static_research_is_idempotent_and_capture_checked(self):
        tool.queue_specimen("revisit", "https://revisit.example.org")
        source = self.example_zip()
        tool.process_specimen("revisit", source)
        tasks = tool.load_json(self.root / "queues/tasks.json")["tasks"]
        old_count = len(tasks)
        self.assertEqual(tool.enqueue_static_for_current_version("revisit", source), 0)
        self.assertEqual(len(tool.load_json(self.root / "queues/tasks.json")["tasks"]), old_count)
        # A different capture must not be silently treated as the same version.
        mismatched = self.base / "mismatch.zip"
        with zipfile.ZipFile(mismatched, "w") as z:
            z.writestr("client.js", "const x = 1;")
        with self.assertRaisesRegex(ValueError, "does not match"):
            tool.enqueue_static_for_current_version("revisit", mismatched)

    def test_static_backfill_reopens_incomplete_source_work(self):
        tool.queue_specimen("reopened", "https://reopened.example.org")
        source = self.example_zip()
        tool.process_specimen("reopened", source)
        doc = tool.load_json(self.root / "queues/tasks.json")
        doc["tasks"] = [task for task in doc["tasks"]
                        if "-followup-static-" not in task["id"]]
        tool.save_json(self.root / "queues/tasks.json", doc)
        record_path = self.root / "specimens/reopened/v0001/record.json"
        record = tool.load_json(record_path)
        record["status"] = "reviewed"
        record["coverage"] = {key: "analyzed" for key in record["coverage"]}
        tool.save_json(record_path, record)
        index_path = self.root / "specimens/index.json"
        index = tool.load_json(index_path)
        index["specimens"][0]["status"] = "reviewed"
        tool.save_json(index_path, index)
        added = tool.enqueue_static_for_current_version("reopened", source)
        self.assertGreater(added, 0)
        self.assertEqual(tool.load_json(record_path)["status"], "researching")
        self.assertEqual(tool.load_json(index_path)["specimens"][0]["status"], "researching")
        self.assertEqual(tool.load_json(record_path)["coverage"]["scripts"], "partial")
        self.assertEqual(tool.enqueue_static_for_current_version("reopened", source), 0)
        self.assertEqual(validator.validate(), [])

    def test_html_input_outside_repo(self) -> None:
        tool.queue_specimen("simple", "https://www.example.com/")
        html = self.base / "saved.html"
        html.write_text("<main><a href='/help'>Help</a></main>")
        tool.process_specimen("simple", html)
        self.assertEqual(tool.load_json(self.root / "specimens/simple/v0001/record.json")["capture_scope"], "saved_page")
        with self.assertRaisesRegex(ValueError, "outside"):
            tool.inspect_capture(self.root / "specimens/simple/v0001/analysis.md")

    def test_zip_traversal_rejected_without_public_changes(self) -> None:
        tool.queue_specimen("reject", "https://example.net")
        with self.assertRaisesRegex(ValueError, "unsafe archive"):
            tool.process_specimen("reject", self.example_zip(unsafe=True))
        self.assertEqual(tool.load_json(self.root / "queues/tasks.json")["tasks"], [])
        self.assertEqual(tool.load_json(self.root / "specimens/index.json")["specimens"][0]["current_version"], 0)

    def test_public_origin_sanitization(self) -> None:
        for invalid in (
            "https://example.org/page", "https://example.org/?" + "token=abc",
            "https://user:pass@example.org", "http://localhost",
            "http://127.0.0.1", "https://internal.local"
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                tool.public_origin(invalid)
        self.assertEqual(tool.public_origin("https://WWW.Example.ORG/"), "https://www.example.org")

    def test_queue_dependency_coverage(self) -> None:
        profiles = tool.load_json(self.root / "queues/profiles.json")["profiles"]
        keys = {p["id"] for p in profiles}
        self.assertGreaterEqual(len({p["queue"] for p in profiles}), 10)
        self.assertGreaterEqual(len(profiles), 15)
        self.assertTrue(all(set(p["depends_on"]) <= keys for p in profiles))


    def test_chat_feature_trace_is_automatically_queued(self):
        source = self.base / "chat.zip"
        with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("index.html", "<main>fictional chat</main>")
            archive.writestr("client.js",
                "function submitMessage(conversationId,messageId){return messageId;}")
        tool.queue_specimen("chatdemo", "https://chatdemo.example.org")
        self.assertEqual(tool.process_specimen("chatdemo", source), 1)
        tasks = tool.load_json(self.root / "queues/tasks.json")["tasks"]
        feature_tasks = [t for t in tasks if "-followup-static-feature-chat-" in t["id"]]
        self.assertEqual(len(feature_tasks), 4)
        self.assertTrue(all(t["status"] == "queued" for t in feature_tasks))
        self.assertTrue(all(t["depends_on"] and t["notes"] for t in feature_tasks))
        self.assertEqual(validator.validate(), [])

    def test_unrelated_site_does_not_get_a_chat_feature(self):
        source = self.base / "plain.zip"
        with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("client.js", "export function draw(){return 42}")
        tool.queue_specimen("plain", "https://plain.example.org")
        tool.process_specimen("plain", source)
        tasks = tool.load_json(self.root / "queues/tasks.json")["tasks"]
        self.assertFalse(any("-feature-chat-" in task["id"] for task in tasks))
        self.assertTrue(any("-followup-static-source-functions" in task["id"] for task in tasks))

    def test_large_vendor_archive_does_not_invent_features_from_one_bundle(self):
        source = self.base / "vendor-rich.zip"
        with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("index.html", "<main>synthetic</main>")
            for i in range(22):
                text = ("const shoppingCart=1, paymentMethod=2;" if i == 0
                        else "export const unrelated = true;")
                archive.writestr(f"part-{i}.js", text)
        tool.queue_specimen("vendors", "https://vendors.example.org")
        tool.process_specimen("vendors", source)
        tasks = tool.load_json(self.root / "queues/tasks.json")["tasks"]
        self.assertFalse(any("-static-feature-commerce-" in x["id"] for x in tasks))
        self.assertTrue(any("-static-source-calls" in x["id"] for x in tasks))
        self.assertEqual(validator.validate(), [])

    def test_large_archive_generates_many_deep_tasks(self):
        source = self.base / "large.zip"
        with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("index.html", "<main>synthetic test</main>")
            for i in range(24):
                archive.writestr(f"bundle-{i}.js", "export const test = true;")
            for i in range(7):
                archive.writestr(f"style-{i}.css", ":root {--test: 1}")
            archive.writestr("icon.svg", "<svg/>")
            archive.writestr("font.woff2", b"not-a-real-font")
        tool.queue_specimen("largesite", "https://large.example.org")
        self.assertEqual(tool.process_specimen("largesite", source), 1)
        tasks = tool.load_json(self.root / "queues/tasks.json")["tasks"]
        deep = [t for t in tasks if "-followup-deep-" in t["id"]]
        self.assertGreaterEqual(len(deep), 55)
        self.assertTrue(all(t["status"] == "queued" and t["notes"] and t["depends_on"] for t in deep))
        self.assertEqual(validator.validate(), [])


if __name__ == "__main__":
    unittest.main()
