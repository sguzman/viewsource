"""Keep the human-readable chat queue status tied to its source of truth."""
from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ChatQueueDocumentationTests(unittest.TestCase):
    def test_readme_progress_matches_queue(self):
        queue = json.loads((ROOT / "queues/chat_research.json").read_text("utf-8"))
        tasks = queue["tasks"]
        complete = sum(x["status"] == "done" for x in tasks)
        runtime = sum(x["status"] == "requires_new_evidence" for x in tasks)
        self.assertEqual(complete + runtime, len(tasks))
        self.assertTrue(all(x["scope"] == "runtime" for x in tasks
                            if x["status"] == "requires_new_evidence"))
        readme = (ROOT / "README.md").read_text("utf-8")
        match = re.search(
            r"tracks \*\*(\d+) completed offline tasks and (\d+) runtime investigations",
            readme,
        )
        self.assertIsNotNone(match, "README queue overview missing or stale")
        self.assertEqual((int(match.group(1)), int(match.group(2))), (complete, runtime))

    def test_runtime_tasks_are_not_labeled_completed_without_evidence(self):
        queue = json.loads((ROOT / "queues/chat_research.json").read_text("utf-8"))
        pending = [x for x in queue["tasks"]
                   if x["status"] == "requires_new_evidence"]
        self.assertTrue(pending)
        self.assertTrue(all(not x["evidence_refs"] for x in pending))


if __name__ == "__main__":
    unittest.main()
