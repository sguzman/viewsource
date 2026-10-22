"""Private ZIP-to-AST integration tests with invented source, never a user capture."""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def parser_installed() -> bool:
    if not shutil.which("node"):
        return False
    result = subprocess.run(
        ["node", "-e", "require.resolve('acorn')"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        check=False, timeout=10)
    return result.returncode == 0


@unittest.skipUnless(parser_installed(), "Node.js Acorn dependency unavailable")
class StaticImplementationArchiveTests(unittest.TestCase):
    def test_private_zip_traces_are_ordinals_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "invented-capture.zip"
            sentinel = "synthetic-private-message-not-for-publication"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("assets/b.js",
                    "async function branch(client,c,m){return client.branch("
                    "{conversationId:c,messageId:m})};")
                z.writestr("assets/a.js",
                    "function factory(){"
                    "function dispatch(x){for(let n=x.regenerateFromMessageId;"
                    "n;){n=x.parentMessageId;if(x.children.length)break;}}"
                    "function submit(x){return dispatch(x)}"
                    "}" + "const original='" + sentinel + "';")
            process = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(archive), "--chat-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=40)
            self.assertEqual(process.returncode, 0, "AST integration probe failed")
            report = json.loads(process.stdout)
            self.assertEqual(report["parsed_bundles"], 2)
            self.assertEqual(report["failed_bundles"], 0)
            self.assertEqual(report["pattern_counts"]["branch_transport_call"], 1)
            self.assertEqual(report["pattern_counts"]["generation_parent_selection"], 1)
            edges = report["direct_call_candidates"]
            self.assertEqual(len(edges), 1)
            self.assertEqual(edges[0]["source_ref"], "R-JS-001")
            self.assertEqual(edges[0]["module_factory_ordinal"], 1)
            self.assertEqual(edges[0]["caller_function_ordinal"], 3)
            self.assertEqual(edges[0]["callee_function_ordinal"], 2)
            self.assertNotIn(sentinel, process.stdout)
            self.assertNotIn("assets/a.js", process.stdout)
            self.assertNotIn(str(archive), process.stdout)

    def test_non_zip_input_is_rejected_without_dumping_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / "private-secret-invalid.zip"
            original.write_text("not a ZIP")
            process = subprocess.run(
                ["python3", str(ROOT / "scripts/trace_static_archive.py"),
                 "--input", str(original), "--chat-trace"],
                cwd=ROOT, capture_output=True, text=True, check=False, timeout=15)
            self.assertNotEqual(process.returncode, 0)
            self.assertNotIn("private-secret-invalid", process.stderr)


if __name__ == "__main__":
    unittest.main()
