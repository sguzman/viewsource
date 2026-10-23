# Research queues

\`profiles.json\` describes the standard analysis task graph. Each processed specimen version creates tasks in \`tasks.json\`; the file begins empty. Queues group work by analytical discipline rather than a single undifferentiated checklist.

Task statuses: \`queued\`, \`in_progress\`, \`blocked\`, \`not_observable\`, \`done\`. A task can be closed as unobservable without fabricating evidence. Tasks can name dependencies; their completion is not inferred from downstream state.

Version-specific task records remain attached to the version that produced them. Follow-up tasks should be unique and cite the parent specimen/version. No source ZIP content, script listings or unreviewed local evidence is added to this file.

## Inspect ready work

Run `python3 scripts/work_queue.py ready` to show tasks whose dependencies are completed or marked not observable. Add `--specimen <slug>` or `--queue <category>` to narrow the list. `summary` groups statuses by queue, and `blocked` shows queued tasks waiting on dependencies. These commands are **read-only** and do not silently claim, complete, or publish any task. Their output consists only of reviewed task metadata already in this repository.

Completed tasks require evidence references drawn from the version's published, sanitized findings. Validation rejects completed tasks with missing or ungrounded evidence references. A task may remain queued even if partial observations have already been recorded.

Capture intake now also reads `static_profiles.json` to enqueue code-level tracing on every qualifying dump, not just the large-archive deep queue. Candidate feature tasks are data-driven and remain distinct from verified functionality. All work uses the same persistent, dependency-aware `tasks.json` graph.

## Static source-research acceptance handoff

For chatgpt.com v0002, run `node scripts/static_acceptance_audit.mjs` for the current open checks, or add `--json` for a machine-readable continuation report. The [acceptance ledger](../specimens/chatgpt-com/v0002/static_acceptance_gaps.json) identifies the missing source-scoped checks for every active task. It neither replaces the canonical queue nor closes tasks on the strength of partial evidence. CI validates the ledger, canonical finding references and task statuses using independent Node.js regression tests. The started percentage means only the proportion of tasks in progress, never overall completion.
