# Chat interactions: research contract

**Objective:** produce a machine-readable, evidence-graded model that can be used to write a chat state graph, a browser adapter, or a test harness. The model must describe behavior, not just libraries or source-code call counts.

The initial [feature graph](../specimens/chatgpt-com/v0002/chat-interaction.graph.json) is a **candidate model** because the saved ZIP contains no recorded chat interaction sequence. It must not be described as the recovered behavior of the live site.

## Model the graph in distinct layers

1. **UI surfaces.** Visible navigation areas, editor, controls, form and dialogs. Each must be linked to a versioned Viewsource ontology component, evidence, and an observed/unknown label.
2. **Domain entities.** Abstract conversation, message, message-parent relationship, selected branch, draft, response attempt. Use only invented local opaque keys in public examples.
3. **State.** Conversation selection is separate from composer/response progress. Keep machine IDs and state IDs stable in the graph even when future research changes confidence.
4. **Events.** Explicit user actions and generic browser/system events, with typed but content-free fields. Do not make a source-method call equivalent to an observed UI event.
5. **Transitions.** From-state, triggering event, to-state, guards, possible side effects, evidence status, and a reproducible way to check the edge.
6. **Dependencies.** Link named libraries to ontology Dependency IDs, while keeping source presence separate from verified ownership of a chat feature.
7. **Runtime evidence.** A future authorized experiment may attach sanitized event timings and state deltas. Do not publish request paths, message bodies, selectors copied from private markup, IDs, headers or payloads.

## Priority behaviors to establish

| Operation | Questions for the research |
|---|---|
| Select conversation | What changes in selected UI, navigation and loaded message graph? What persists across reload? |
| Begin new conversation | When is a new conversation identity established? Can an unsent draft exist without one? |
| Edit composer | Which interactions change draft state and submit availability? How do attachments affect this? |
| Submit message | Does the UI optimistically add a message? When does sending become receiving? How are attempts correlated? |
| Receive response | How do partial updates, final completion, interruption and failure appear in UI state? |
| Stop/retry | Does a retry reuse an existing response, create a new attempt, or create a new message? |
| Edit a prior message | Does editing change an existing node or produce a new child/path? Which prior nodes remain accessible? |
| Regenerate/switch branch | Are alternatives peers under the same parent, and how is the selected path represented? |
| Navigate and persist | Which state is local, which lasts after reload, and which depends on the server? |
| Failure and recovery | Which transitions are reversible and what errors or pending states can be observed? |

This table is an **experiment queue**, not a list of verified capabilities.

## Minimum evidence for a verified transition

A future controlled test should establish the following without exposing private data:

- The abstract state before an action, with the UI region identified.
- One specifically described, authorized and synthetic action.
- The observed UI changes and their ordering, using labels and redacted local correlation keys.
- Any observed route-state *shape* changes, never literal route values.
- Where permitted and necessary, a generic request/stream event classification without URLs, headers, cookies, bodies, tokens or message text.
- Terminal result, repeatability, and whether reloading alters the result.

If any step cannot be established, the transition remains a hypothesis. For inferred effects, explain why; never substitute plausible behavior for an observation.

## Consumer contract

Code can load the standalone JSON emitted by the site under `data/features/`. The structure provides `entities`, `machines`, `events`, `transitions`, `technology_links`, `surfaces`, and `open_questions`. Consumers should:

- Construct state nodes keyed by `machine + state` rather than one global state string.
- Build directed edges from `from`, `event`, and `to`, retaining guards, effects, verification guidance and evidence status.
- Render `hypothesis` edges distinctly from `observed_live` edges. **Do not activate an automated site interaction solely because a hypothetical edge exists.**
- Treat `branch_model` as unresolved until future evidence establishes parent/alternative/selected-path semantics.
- Keep private traces, identity mappings and user content in a separate local workspace, outside public Viewsource publications.

This contract is deliberately independent of any particular browser automation library or web framework.
