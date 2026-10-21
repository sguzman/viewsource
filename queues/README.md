# Research queues

\`profiles.json\` describes the standard analysis task graph. Each processed specimen version creates tasks in \`tasks.json\`; the file begins empty. Queues group work by analytical discipline rather than a single undifferentiated checklist.

Task statuses: \`queued\`, \`in_progress\`, \`blocked\`, \`not_observable\`, \`done\`. A task can be closed as unobservable without fabricating evidence. Tasks can name dependencies; their completion is not inferred from downstream state.

Version-specific task records remain attached to the version that produced them. Follow-up tasks should be unique and cite the parent specimen/version. No source ZIP content, script listings or unreviewed local evidence is added to this file.
