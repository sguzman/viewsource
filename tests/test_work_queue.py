"""Pure functional dependency-readiness checks."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

repo = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("work_queue", repo / "scripts/work_queue.py")
queue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)


class QueueTests(unittest.TestCase):
    def test_ready_and_blocked(self):
        examples = [
            {"id": "a", "specimen_id": "demo", "version": 1, "queue": "intake", "status": "done", "depends_on": []},
            {"id": "b", "specimen_id": "demo", "version": 1, "queue": "styles", "status": "queued", "depends_on": ["a"]},
            {"id": "c", "specimen_id": "demo", "version": 1, "queue": "styles", "status": "queued", "depends_on": ["b"]},
            {"id": "d", "specimen_id": "demo", "version": 1, "queue": "styles", "status": "not_observable", "depends_on": []},
            {"id": "e", "specimen_id": "demo", "version": 1, "queue": "styles", "status": "queued", "depends_on": ["d"]},
        ]
        self.assertEqual(queue.classify(examples, examples[1]), "ready")
        self.assertEqual(queue.classify(examples, examples[2]), "blocked")
        self.assertEqual(queue.classify(examples, examples[4]), "ready")
        self.assertEqual(len(queue.choose_tasks(examples, queue="styles")), 4)
        self.assertEqual(len(queue.choose_tasks(examples, specimen="other")), 0)


if __name__ == "__main__":
    unittest.main()
