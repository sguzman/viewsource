#!/usr/bin/env python3
"""Read-only, dependency-aware research queue viewer."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SATISFIED = {"done", "not_observable"}


def choose_tasks(all_tasks, specimen=None, queue=None):
    return [t for t in all_tasks if
            (specimen is None or t["specimen_id"] == specimen) and
            (queue is None or t["queue"] == queue)]


def classify(all_tasks, candidate):
    by_id = {t["id"]: t for t in all_tasks}
    unsatisfied = [d for d in candidate["depends_on"]
                   if d not in by_id or by_id[d]["status"] not in SATISFIED]
    if candidate["status"] == "queued":
        return "blocked" if unsatisfied else "ready"
    return candidate["status"]


def display(command, all_tasks, subset):
    counts = Counter()
    grouped = defaultdict(list)
    for task in subset:
        derived = classify(all_tasks, task)
        counts[(task["queue"], derived)] += 1
        if command in {"ready", "blocked"} and derived == command:
            grouped[task["queue"]].append(task)
    if command == "summary":
        for queue in sorted({t["queue"] for t in subset}):
            groups = ", ".join(f"{state}={counts[(queue,state)]}"
                               for state in ("ready", "blocked", "in_progress", "done", "not_observable")
                               if counts[(queue,state)])
            print(f"{queue}: {groups}")
        if not subset:
            print("No tasks matched.")
    else:
        if not grouped:
            print(f"No {command} tasks.")
        for queue in sorted(grouped):
            print(queue + ":")
            for task in sorted(grouped[queue], key=lambda x: (x["specimen_id"], x["version"], x["id"])):
                label = " (limited by unobservable dependency)" if any(
                    next((d["status"] for d in all_tasks if d["id"] == dep), "") == "not_observable"
                    for dep in task["depends_on"]
                ) else ""
                print(f"  {task['id']}: {task['title']}{label}")


def main():
    parser = argparse.ArgumentParser(description="Read-only research queue readiness")
    parser.add_argument("command", choices=["summary", "ready", "blocked"])
    parser.add_argument("--specimen", help="Restrict to an existing specimen slug")
    parser.add_argument("--queue", help="Restrict to a research topic queue")
    args = parser.parse_args()
    doc = json.loads((ROOT / "queues/tasks.json").read_text(encoding="utf-8"))
    tasks = doc["tasks"]
    subset = choose_tasks(tasks, args.specimen, args.queue)
    display(args.command, tasks, subset)


if __name__ == "__main__":
    main()
