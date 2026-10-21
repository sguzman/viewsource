# Research queues

\`profiles.json\` describes the standard analysis task graph. Each processed specimen version creates tasks in \`tasks.json\`; the file begins empty. Queues group work by analytical discipline rather than a single undifferentiated checklist.

Task statuses: \`queued\`, \`in_progress\`, \`blocked\`, \`not_observable\`, \`done\`. A task can be closed as unobservable without fabricating evidence. Tasks can name dependencies; their completion is not inferred from downstream state.

Version-specific task records remain attached to the version that produced them. Follow-up tasks should be unique and cite the parent specimen/version. No source ZIP content, script listings or unreviewed local evidence is added to this file.

## Inspect ready work

Run `python3 scripts/work_queue.py ready` to show tasks whose dependencies are completed or marked not observable. Add `--specimen <slug>` or `--queue <category>` to narrow the list. `summary` groups statuses by queue, and `blocked` shows queued tasks waiting on dependencies. These commands are **read-only** and do not silently claim, complete, or publish any task. Their output consists only of reviewed task metadata already in this repository.

Completed tasks require evidence references drawn from the version's published, sanitized findings. Validation rejects completed tasks with missing or ungrounded evidence references. A task may remain queued even if partial observations have already been recorded.
