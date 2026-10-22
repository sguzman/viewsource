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

## Static chat controls found in the v0002 ZIP

The saved rendered HTML contains one contenteditable textbox inside the form under main. Generic edit-related and regenerate-related labels occur on four main-region buttons each. Copy-related labels occur on eight main-region buttons, and new-chat-related labels appear on navigation and header buttons. Counts are label occurrences, not guaranteed distinct actions; neither actual click outcomes nor message ownership was traced.

The feature graph therefore includes a separate **message edit and regeneration** candidate machine, distinct from composer sending and conversation selection. Its transitions cannot be promoted to `observed_live` without independently verified event and state changes.

## Public product documentation versus internal source

OpenAI's public ChatGPT release notes announced a web UI action to branch a conversation into a separate chat on September 4, 2025: https://help.openai.com/en/articles/6825453-chatgpt-release-notes . This establishes a documented user-facing action, not the server-side representation, identity mapping, message ancestry or persistence. The research model keeps separate-conversation forks distinct from alternative messages within one conversation. Neither internal relationship is asserted as verified by that documentation.

## Code-consumer tools

A standard-library reader at `scripts/chat_feature_cli.py` exports machine-scoped transition metadata and DOT graphs. Use `--machine response --format dot` for a candidate response state diagram; `--machine message_operation --format json` lists unverified edit/regeneration steps; `--domain --format dot` shows the entity-to-entity relationship graph. The default execution-verification path fails closed: `--resolve-verified` rejects every edge in the current snapshot because none has independent live evidence. These interfaces perform no browser operations.

A separate synthetic model at `scripts/chat_graph_core.py` demonstrates immutable parent links, visible selected paths, alternative replies and cross-conversation fork annotations without storing any chat text. Fork annotations do not clone messages or claim a specific remote implementation.

## Using the candidate graph for software

These tools describe *possible* structures. They are not browser automation and cannot verify the site's internal API.

- `scripts/chat_graph_core.py` builds synthetic message ancestry and separate-conversation fork examples. `anonymous_topology()` emits temporary ordinal-only graph structure, discarding supplied local keys. Ordinals must never be assumed stable across independently generated graphs.
- `scripts/chat_feature_cli.py --domain --format dot` generates a hypothetical entity relationship diagram; `--machine response --format dot` generates the response machine.
- `scripts/simulate_chat_scenario.py examples/chat_scenario_synthetic.json --assume-guards` exercises a fictional interaction sequence across separate machines. Guard assumptions are explicit; without the flag, guarded edges are rejected. It performs no site actions and reports zero verified behavior.
- `scripts/validate_chat_observation.py` accepts only fixed structural-event fields in a disposable synthetic test record. `scripts/analyze_chat_observation.py` can then compare the fixed event categories with candidate graph transitions. It does not infer causal ownership or promote a transition to verified.

## Three separate evidence layers

The [capability matrix](../specimens/chatgpt-com/v0002/chat_capability_matrix.json) maps eight chat operations across static evidence, public product documentation, candidate graph references, and the specific unanswered question. The [public chat actions](../specimens/chatgpt-com/v0002/public_chat_actions.json) are documented user-interface behaviors from the official Help Center; they are not derived from the private capture and do not expose any server implementation. The [feature graph](../specimens/chatgpt-com/v0002/chat-interaction.graph.json) remains entirely hypothetical for message ancestry and runtime transitions.

The website includes a synthetic branch-selection visualization. Its messages, alternatives and separate conversation fork are invented for demonstration, **not** extracted from a user's chats.

A future controlled test should yield content-free structural evidence and independent verification. Until then, the current research has no verified live transition, request contract, response stream grammar or backend message identity mapping.

## Publicly described export tree (separate from captured runtime)

OpenAI documents an export containing conversation JSON. Independent public
parsers describe a tree-shaped export in which `mapping` holds nodes with
`parent` and `children`, while `current_node` selects the current ancestry
path. See [the source-classified report](../specimens/chatgpt-com/v0002/export_format_research.json).

The local `scripts/inspect_chat_export.py` tool can inspect an export shard
without printing conversation titles, message content, node identifiers, or
conversation IDs. It only emits aggregate tree statistics and validation
counts. It incrementally parses top-level export arrays using the Python standard library; memory use grows with the largest individual record, not the entire file. The input reader rejects duplicate JSON object keys and nonstandard non-finite numbers, while the tree audit distinguishes duplicate child references from genuine alternatives. Never commit,
upload, or redirect real exports or detailed analyses into the public
repository. No real export was used for the tests.

Community documentation warns that private API responses may now use
flat message arrays rather than legacy tree mappings. The analyzer does not
invent parent links for such arrays. Neither format should be described as
proven backend storage or as the implementation observed in v0002.

## Normalizing an exported tree without original IDs

`scripts/normalize_chat_export.py` provides the pure function
`normalize_conversation(record)` for one tree-shaped export record. It
validates reciprocal parent/child links, selected-node ancestry and cycles,
then generates ordinal-only nodes, roles, parent links and selected paths.
Real message text, titles, conversation IDs, and original node IDs never
appear in its result. The function handles a selected internal node without
mistaking it for a leaf.

There is intentionally **no command-line entrypoint** to print a complete
real user's per-conversation graph. The `inspect_chat_export.py` CLI is
restricted to aggregate counts. Local consumers may call the normalizer
explicitly, but must not publish or log derived private graph structures.

This is an adapter for community-documented export trees only. It does not
validate ChatGPT's current browser interaction protocol or backend model.

## Comparing two anonymous export topologies

`scripts/compare_chat_topologies.py` compares two results from
`normalize_conversation()` in memory, without assuming their temporary
ordinals correspond. Its bottom-up subtree comparison is independent of node
identifiers and source mapping iteration order. It reports whether the
actor-labeled forests are structurally equivalent, whether marking the
selected ancestry paths preserves that equivalence, and aggregate metric
deltas. It validates parent links, selection ancestry, branch counts and
cycles before comparing. Deep graphs are handled iteratively.

This is **not** an identity join, operation classifier, or browser trace.
Two symmetrical alternatives can be indistinguishable even if the selected
reply changed. Changing topology cannot, by itself, distinguish editing,
regeneration, a new reply, or an export-format change. No fingerprint, node
identifier, source message, or per-message comparison is returned. The
comparator has no CLI and is for deliberate local, synthetic or explicitly
authorized data processing only; never publish output from a personal export
without separate review.

## Trustworthy structural event comparisons

The structural trace parser in `validate_chat_observation.py` accepts only
bounded, unique-key, standards-compliant JSON. Its CLI and the event analyzer
use fixed error messages rather than printing the supplied path or parser
fragments. The sequence analyzer treats `not_observed` and `inconclusive`
results as non-confirming even when a separate coarse state label resembles
the target of a candidate transition. The before/after labels remain
independent UI observations; no event alignment proves an internal handler.

## Synthetic browser scenario coverage

The Playwright suite uses only `tests/fixtures/synthetic-chat.html`, a
locally authored fictional page. Its four independent scenarios are:
completed response followed by a fictional separate conversation, stopped
response, failure during receiving followed by retry and completion, and
failure during sending before partial output. The suite also rejects a
retry with no failed attempt. Every emitted trace goes through both the
strict structural validator and candidate-event analyzer. CI asserts
synthetic counts and sequencing but never promotes these scenarios to
observed live ChatGPT behavior.

## Proposed runtime study protocols

`queues/chat_runtime_protocols.json` now provides one strictly hypothetical
study plan per unresolved runtime task. Each contains a research question,
contrasting possible outcomes, allowed structural observation categories and
a stop boundary. The builder requires exactly one plan per open task, and
the atlas shows the plan within its backlog item. These proposals are **not**
recordings, browser selectors or permission to experiment. Every live
investigation still requires separate, explicit authorization for a
disposable synthetic session. A protocol can be completed only after
independently reviewed evidence; proposed alternatives must never be
promoted to verified findings.

## Distinct flat-message input shape

Community research describes some private endpoint responses containing
`messages` arrays instead of legacy `mapping` trees. This is not
proof that a current ChatGPT data export has the same format. The local
inspector now reports `flat_message_items` as a separate aggregate for
array-shaped inputs while leaving tree nodes, parent links, alternatives
and selected-path status unestablished. A flat array must never be silently
treated as a tree or used to infer a branch switch.

## Linear-time local JSON record scanning

The export-array reader scans strings, escapes and container depth only once
to locate each top-level record boundary. It then calls the strict JSON
decoder once per completed record, instead of repeatedly decoding an
unfinished growing record after every read. Processing remains incremental
over the top-level array and bounded by the largest individual record
(current safety cap: 128 MiB of characters). Malformed or duplicate-key
records still fail closed. This does not parse or infer undocumented
message ancestry in a flat response.
