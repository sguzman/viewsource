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

## Newly queued source-first continuation

The original captured JavaScript is accessible for further analysis. The specimen's initial audit and its 91 terminal tasks remain in the historical record, while 33 new static research tasks are now queued in `queues/tasks.json`. The current capture has returned to `researching` because function call chains, domain shapes, UI handlers, streaming, retries, and persistence have not yet been fully traced. The optional runtime research queue does not block this source-first work.

## New AST-anchored static findings

The source-first follow-up now includes a [sanitized AST report](../specimens/chatgpt-com/v0002/chat_ast_followup.json) derived from the original captured JavaScript. All 144 JavaScript files parsed successfully; the private analysis identified 333 candidate structural functions across 41 bundles. The report records literal member-property pairs and assignments, including `conversationId`/`messageId`, `mapping`/`current_node`, and `parent`/`children`. It does not publish source snippets, site identifiers, URLs or source locations. These **are concrete syntax-level observations, not verified chat-function ownership**. The next tasks must resolve call edges and data flow before promoting any chat state claim.

## Reproducible source-local AST traces

The `scripts/trace_chat_impl.cjs` parser recognizes three narrow, inspectable
client-code shapes: a `current_node`/mapping/parent ancestry walk inside a
loop, an object-argument branch call containing conversation and message
identities, and a mapping reconciliation that references children, parents,
and selection. Output contains only captured-resource ordinals, ordinal
function indices, lexical enclosure and allowlisted pattern labels.
These are syntax matches, **not automatically proven chat handlers**.

To reproduce the aggregate candidate report entirely offline, use
`python3 scripts/trace_static_archive.py --input /path/to/saved.zip --chat-trace`
with Node.js and the project's Acorn developer dependency installed. The
ZIP is read under a temporary private directory; its scripts are never
executed or copied into the repository. For this specimen, function
ordinals are one-based indices in a deterministic AST pre-order within
captured JavaScript resources sorted by original archive name.

## Reviewed static module export bindings

AST-backed source review also identified four captured module export getters
exposing the selected-path, predicate-limited ancestry, conversation-refetch,
and branch operations. Each relationship is recorded by module factory and
function ordinal in the sanitized implementation-trace report. The export
bindings establish that the relevant functions are exposed within these
captured bundles; the identity and actual execution of importing UI code
remain open research tasks, not established runtime behavior.

## Regeneration and generation-branch selection

Further AST inspection of the original captured bundles has established two
additional client-side source implementations: one generation-dispatch
function combines explicit continuation/parent parameters, regeneration
inputs and pre-existing child-branch information to choose a parent
message; another constructs and dispatches a regeneration operation using
the targeted message identity and regeneration options. Both are recorded
by capture-local function ordinal in the static implementation trace.
These are **source statements about possible client execution paths**, not
observations of a regeneration happening on the live service.

## Direct generation-dispatch calls

The captured module contains a shared generation-dispatch function and
four client entrypoints that call it directly: normal completion, local
function-result submission, regeneration, and a conditional retry path.
All five functions are inside a single captured module factory. The
first three entrypoints have descriptive static module export bindings.
These four caller-to-callee edges are reviewed source-level facts, not
merely co-occurring field names or a speculative state diagram. They
still do not demonstrate that any particular pathway was exercised in
a live session or reveal server storage semantics.

## Automated conservative caller discovery

The AST tracer now discovers same-module direct identifier calls into the
generation-parent-selection routine without publishing original symbol names.
On this capture it identifies six such candidate callers. Four have been
individually reviewed against their source-level behavior; two have not yet
been classified. A lexical named call in one module does not independently
verify dynamic execution. Unreviewed caller edges are preserved as candidates
rather than assigned invented product responsibilities.

## Completed first-pass dispatch call classification

The two initially unclassified same-module callers were independently
examined in the saved source. One wraps a work-handoff conversion carrying a
parent/handoff reference and message; the other issues a continuation with
an answer-now steering setting. All six detected caller-to-dispatcher edges
are now manually reviewed, with their source ordinals and export statuses
recorded. This completes the **local call-edge classification for this
specific generation dispatcher**, not the overall ChatGPT static research.
Cross-module callers, live execution and backend behavior remain open.

## Static tracing work in progress

The newly generated tasks for implementation-function classification,
direct source call tracing, and chat feature operations have moved from
`queued` to `in_progress`. Source-anchored evidence now exists, but none
has been marked `done` because caller coverage and complete handler
ownership have not met the acceptance requirements. Other static tasks
remain queued, and runtime observation remains optional.

## Transport, resumption and cancellation source trace

The [transport trace](../specimens/chatgpt-com/v0002/chat_transport_trace.json)
documents five directly inspected client methods from captured JavaScript
resource R-JS-018: starting a completion stream, resuming a completion
stream, canceling a stream, obtaining stream options, and constructing stream
handlers. Eight source-level relationships distinguish direct calls,
conditional topic-versus-request resume routes, local/request cancellation,
and recovery configuration.

A separate static WebSocket item handler tracks previously seen item
identities, duplicate-item suppression and missing-parent checks before
forwarding decoded events. The saved client also declares retry, timeout,
resume-token, and lifecycle callback support. None of these implementation
facts verifies server delivery, persistence or which transport an actual
session selects.

The offline ZIP inspector now supports `--transport-trace`, which parses
saved JavaScript without executing it and emits allowlisted transport method
and callback signals without source text or network details. The dedicated
report includes manually reviewed behavior and explicit remaining gaps; AST
signal presence alone is not sufficient evidence of a working live path.

## Generation-to-transport source linkage

Further inspection of the original captured module found a direct call
from the shared generation dispatcher (R-JS-018, function ordinal 9032)
to the completion stream service's `startCompletionStream` method. The
caller passes callbacks for decoded events, raw stream data, stream
completion, premature termination, recoverable errors, response metadata
and resumption. A recovery pathway reads the currently selected node and
message mapping from client state. This is a concrete source-level bridge
between the generation call graph and the transport lifecycle, not merely
shared vocabulary. A direct scoped-service call in the bundle still does
not prove the real service delivered a response or that a backend persisted
a particular message graph.

## Decoded stream events into message updates

The generation dispatcher supplies an event processor's `onEvent`
method to the transport's `onDecodedEvent` callback. The processor is
constructed with an `onUpdate` handler. In that handler, message-class
updates feed message and model-message callbacks; marker-class updates
feed timing and render-marker tracking, while terminal/statistics updates
follow separate paths. These connections are directly represented by
captured source and now form two additional evidence-graded edges in the
transport trace. The processor's imported implementation, eventual
message-store writes, and selected-message rendering remain unresolved.

## Message update batching and client-state helper invocation

The event processor used by the generation dispatcher is also present in
the saved JavaScript. Its decoded-event handler classifies message updates,
passes submission messages through a batching callback, and may defer some
resumed-message updates for replay. Its `applyMessage` method checks
message-placement acceptance and invokes an imported client-state mutation
helper with the conversation, message, preserve-current-turn setting and
optional fallback parent reference.

This gives a **source-verified path** from the generation dispatcher through
transport callbacks, decoded event handling and message-state mutation
invocation. The imported helper's internal reducer/storage operation and
eventual UI updates are still open static-analysis tasks. Neither a server
write nor an actual browser state change has been observed.

## Recovered message graph mutation and selection logic

A deeper source trace reaches the imported mapping transformer called by
the event processor's state writer. The transformer receives the existing
message mapping, an incoming message, and a fallback parent identity;
it returns a revised mapping, message identity, new-node flag, and
descendant-rotation flag.

The captured implementation updates existing or missing nodes, chooses
parent relationships with metadata and ancestry guards, repairs child lists
when reparenting, and handles a special merged-fragment continuation case.
A higher-level state writer uses the resulting graph together with
preserve-current-turn intent, selected ancestry and optimistic-local
message state to decide the next selected node and publish the updated
conversation state. Its return value exposes the previous and next
client state.

The [sanitized graph mutation study](../specimens/chatgpt-com/v0002/chat_graph_mutation_trace.json)
enumerates nine source-backed operations and six function-level edges.
This is a captured client algorithm, not merely a candidate graph model.
It does **not** establish that arbitrary malformed mappings are always
repaired, how the backend stores messages, or whether a particular live
action selected a given branch.

## Expanded active source investigations

The source-level studies for streaming/resumption, message data shapes, and
chat feature data-model operations are now in progress alongside the three
earlier source-function/call/feature tasks. None is marked complete merely
because one recovered function or source edge exists. Current static queue:
6 in progress, 27 queued, 0 complete. Dependency and acceptance contracts
remain unchanged.

## Scoped state commit and visible ancestry projections

The next saved-source function in the same capture takes the updated
conversation state and writes the mapping and current node into a scoped
client store. It also maintains separate selected-path automation-reference and
page-reference collections, and a root-to-leaf user-message ancestry list
updated after relevant selection/parent changes. The automation scanner
extracts references from metadata, supported widgets and tool results;
the page scanner extracts eligible page resources. **Neither is the main
visible-message transcript.** The
user-message traversal protects against revisiting a node. These are source-backed client projections with distinct purposes.
Their consumer components must be traced before making UI-rendering claims. Concrete render selectors remain an active
research question.

## Canonical evidence references for partially completed static tasks

Five source-reviewed findings (E2-071 through E2-075) now live in the
specimen's main `record.json` evidence ledger. The six in-progress source
investigations link to those findings even while their broader acceptance
criteria remain unsatisfied. The queue validator now verifies **all**
nonempty task evidence references, including partial in-progress work; it
still refuses to close a task at 100% without valid evidence. Queued and
not-observable tasks cannot carry evidence references. The Atlas displays
the number of grounded findings associated with each static task without
publishing source code or private identifiers.

## Correction: selected-path projections are feature references, not transcript

Follow-up inspection of the exact selected-path collector implementation
established that the collector previously labeled `visible-message`
actually extracts **automation references** from message metadata, tool
results and widget data. A separate collector scans the selected ancestry
for eligible page references. The **user-message ancestry** projection is
independent and remains source-supported. The main chat transcript renderer
has **not** been recovered from these collectors. Canonical finding E2-074,
the mutation study, and their Atlas projection have been corrected rather
than preserving an unsupported interpretation of the code.

## Verified selector consumers (static code only)

A source follow-up identifies two true message-path selectors: the full
root-to-selected-node ancestry and a recent-turn path that stops at a
matching user message. These selectors derive from the message mapping and
current selected node; unlike feature-reference projections, they return
message objects. A captured React conversation-control component uses a
scoped subscription to the recent-turn selector when evaluating skip or
answer-now actions. Composer-related state and other feature selectors
also read recent-turn or full-ancestry messages. Separate consumers read
selected-branch user-message identities for eligibility and automation
references for feature-specific views. These connections are documented in
[chat_selector_consumers.json](../specimens/chatgpt-com/v0002/chat_selector_consumers.json)
and canonical finding E2-076. The main rendered transcript and full
component rendering policy remain open research questions. The source
research queue is now 7 in progress, 26 queued, none completed.

## React control click dispatch recovered from source

The current-turn-subscribed React control binds the same guarded click
handler to inline and Escape-dialog button surfaces. The handler distinguishes
answer-now steering (requires the relevant asynchronous task identity) from
skip-reasoning (requests response stop and, after the stop callback and state
checks, submits a reasoning-skipped regeneration). Its failure path clears
pending-action state and shows an error notification. This evidence is
recorded in canonical finding E2-077 and the selector-consumer study. The
captured JSX and client calls establish implementation wiring, **not**
that a real user saw or exercised either action or that the server accepted
it. Wider component-rendering and event paths remain active work.

## Main transcript turn and message renderer (source-backed)

The saved archive now supports a seven-stage rendering path across captured
resources R-JS-018, R-JS-069 and R-JS-072. A conversation page prepares
`renderedTurns` from the mapping/current selection; the core derivation
builds typed turn items (user and assistant messages, reasoning, tool
activity and media). A preparer can append a temporary pending user item.
The per-turn prop mapper applies a presentation-only option to hide the
first user item, sets last-turn-only status and pending controls, and
computes display timestamps. The page passes prepared turns into the turn
configurator. A turn renderer dispatches items by kind; a nested JSX wrapper
adds message role, source-message IDs and a test selector to rendered elements.

These details are recorded in
[chat_transcript_render_trace.json](../specimens/chatgpt-com/v0002/chat_transcript_render_trace.json)
and canonical evidence E2-078. The trace demonstrates a client rendering
implementation, not a reproduced page, current backend behavior, or all
dynamic-import edges. The earlier automation/page-reference collector
correction remains in force: those collections are **not** the transcript.

A subsequent source check verified the previously missing direct module
relationship: the page-level turn-entry component in R-JS-072 imports the
exported typed turn renderer from R-JS-069 and supplies the configured
turn, conversation context, display flags and callbacks. The public trace
now contains ten reviewed relationships, including this imported-component
edge. This confirms the main page-to-typed-renderer *source wiring*;
dynamically imported subrenderers and actual runtime visibility remain
unverified.

## Source-reviewed transcript display conditions

Nine additional rules in the transcript research artifact separate
conditional **presentation** from underlying conversation data: pending
prompt admission and loading, optional first-user-item suppression,
last-turn-only status/attachments, alternate selected-message rendering,
special sidebar or moderation item classification, reasoning/tool status,
message DOM identifiers, and telemetry wrapping. These are grounded in
saved resources R-JS-018, R-JS-069 and R-JS-072 and canonical evidence
E2-079. They are inspected code paths, not exhaustive runtime behavior;
removing an item from the display list does not prove deletion from the
message mapping. The Atlas now exposes each rule and its limitations.

## Typed renderer edit/regenerate/fork callback guards

Static inspection of the typed turn-renderer module confirms that the
conversation page's edit, regeneration and fork callbacks are forwarded to
message and turn-action components. User editing requires a suitable
user-message item and selected identity; targeted replies and certain
attachments suppress editing. Regeneration is also hidden for read-only
or special-turn states. The fork callback is forwarded to the action row,
subject to its own display guards. Canonical evidence E2-080 records these
callback pathways without asserting any click, network request or server
outcome. Three guarded bindings are visible in the transcript study.

## Response-version selection, optimistic state and rollback

A source-level response-version control uses an ordered variant list,
active index and previous/next buttons. Selection dispatches a variant
identity to an imported client helper that looks up a permissible selected
descendant, changes the local selected-node state immediately, constructs a
conversation-selection persistence request, and rolls back to the prior
selection if the request fails while the optimistic selection remains
current. Its cleanup reconciles conversation state and clears a busy flag.
The seven-stage [branch switch study](../specimens/chatgpt-com/v0002/chat_branch_switch_trace.json)
tracks these client relationships across saved resources R-JS-069 and
R-JS-018. Canonical evidence E2-081 does **not** claim that the server
accepted a switch or that a selection survived reload. Two more static
research tasks (client state flows and network request construction) are
now in progress, bringing the source queue to 10 in progress and 23 queued.

## Response variant eligibility from selected graph ancestry

The saved response-version selector obtains a candidate response node and
walks its parents to a qualifying earlier prompt. It enumerates that
prompt's mapping children as raw response candidates, then filters
candidate descendants to produce the displayed selectable variant list.
The active variant index reflects the current selected path; it can be
unavailable when no eligible candidate matches. Therefore, **raw child
count is not necessarily the displayed response-version count**. This
client-side branch-index derivation is documented with five explicit
steps and canonical evidence E2-082, separately from the optimistic
selection/persistence pathway in E2-081. No actual server response was
observed.

## Selected-branch changes as inputs to transcript derivation

The main conversation page's saved JSX and memo-cache checks explicitly
include both its active `threadCurrentNode` and `threadMapping` inputs
when deriving the rendered conversation and turn list. Those input
references are compared as memoization dependencies alongside pending
prompt, streaming, moderation and conversation context. The resulting
`renderedTurns` then feed the previously verified page-to-turn-renderer
import. This creates a concrete **source-level dependency connection** from
the response-version state-selection algorithm (E2-081/E2-082) to the
transcript-rendering stage (E2-078/E2-083). It does not prove that a real
button click caused a displayed animation or that a server accepted or
persisted the response selection.

## Captured transcript virtualization and scroll placement (E2-084)

A direct source pass through R-JS-072, R-JS-066 and R-JS-069 identified
turn-level virtualization **after** the page derives `renderedTurns`.
The page adapter feeds prepared turn entries and retained turn keys to the
virtualized window. That window computes row offsets from measured or
estimated turn heights, locates the visible range via binary search, and
adds an overscan of two turns. It creates keyed row wrappers positioned
within a total-height region and separately retains eligible turns outside
the normal window. Row measurements and viewport resize observations feed
scroll-distance-from-bottom compensation, history boundary signals, and
programmatic target-turn positioning.

A distinct page hook and response-spacer controller place selected user
turns in some voice-conversation conditions, grow/shrink bottom spacing,
and cancel automated placement after direct user input. The implementation
includes a reduced-motion path. These are **client algorithms** recovered
from captured code, not an observed scroll session; the exact installed
feature settings and server-side history/pagination outcomes remain
unverified. The [sanitized viewport trace](../specimens/chatgpt-com/v0002/chat_viewport_virtualization_trace.json)
contains eleven individually described source rules and seven linking steps.
This addresses the previous question of whether a virtualized turn list
exists while leaving actual browser reconciliation and accessibility
behavior open.

## Branch selection to virtualized row reconciliation (E2-085)

The source-reviewed optimistic response selector changes a candidate
selected current node. The conversation page's memoized turn derivation
reads that selected node and mapping, and the resulting keyed turns feed
the virtual row window. The window compares new turn keys to prior keys;
when possible it retains a surviving rendered anchor key/window span and
compensates distance from the scroll bottom when geometry changes.
This is a composed **static client call/dataflow path**, not evidence
that a particular branch switch occurred, an anchor survived, or the
user saw smooth scrolling. The selection helper may also roll back on
a failed persistence request. See canonical E2-085 and the four-stage
`selected_branch_window_reconciliation` entry in the viewport trace.

## Composer submission to response-spacer lifecycle (E2-086)

The saved conversation composer invokes the response-spacer placement
routine on accepted submission and clears spacer state on submission
errors. The virtual transcript adapter forwards the latest turn's measured
height growth to the spacer's `consumeGrowth` callback. A separate
spacer-controller path interrupts placement and trims remaining space
when the user scrolls away. Four explicit client callback relationships
are recorded in `composer_spacer_wiring` within the viewport study.
No accepted submission, user scroll event, or browser animation was
executed or observed, and runtime presentation flags can choose a
different layout. This adds canonical E2-086 without closing ongoing
source-rendering or state-flow tasks.

## Independent structural AST reproduction of viewport clues

The new viewport AST classifier was rechecked against four named-by-ordinal
modules in the original private capture: R-JS-066 modules 9 and 14,
and R-JS-072 modules 13 and 14. The allowlisted scanner reported eleven
candidate pattern matches (seven, one, one and two respectively),
covering row layout, overscan, offscreen retention, resize, scroll anchoring,
history boundaries, spacer control and manual input cancellation.

This is **syntax-level corroboration** only. The independent manual source
review is the basis for the public algorithm descriptions. The scanner
reports category counts and module ordinals, not the original asset files,
minified module names or code. Candidate counts should never be used as a
surrogate for completed source research or runtime verification.

## Markdown selection and last-code-block command (E2-087, E2-088)

In captured resource R-JS-072, the selected-text popover validates a
noncollapsed DOM range entirely inside one connected assistant Markdown
container, checks conversation/message attribution, and excludes overlapping
writing blocks, learning views, editable controls, and explicit copy-excluded
nodes. It can forward the selected text with a message identity and source
occurrence or load optional side-panel actions. Expanded-detail eligibility
has its own assistant-author gate; it is **not** a blanket gate on all
selection callbacks. This source path was not exercised in a browser.

A separate copy-last-code command walks rendered turns/items backward to
find an eligible assistant code block or structured reference. Resolved
content can be copied directly; for eligible incomplete content, a private
history/content fetch may run under AbortController guards for changes in
conversation, selected node and command state. A separate copy helper
can report success and telemetry. Neither the actual operating-system
clipboard result nor a server content fetch has been observed. The
sanitized [selection/copy study](../specimens/chatgpt-com/v0002/chat_selection_copy_trace.json)
records 13 distinct client stages and explicit uncertainty boundaries.

## Source-reviewed user-message edit lifecycle (E2-089)

The typed turn renderer gates user-message editing by item type, message
identity and special reply/attachment restrictions. The page-level edit
submission routine enforces busy/origin checks, resolves the target's
selected model and original parent, validates a trimmed replacement
message including non-text attachments, optionally stops an incompatible
active response, and revalidates the target after awaiting stop/closure.
It then submits a new completion with the original parent message
identity, selected model and replacement content. A finally block clears
edit-busy state; an outer callback surfaces classified edit errors as a
toast. This does **not** prove the server performed a destructive edit or
accepted a new branch. See the [edit submission trace](../specimens/chatgpt-com/v0002/chat_edit_submission_trace.json).

## Source-reviewed accessible transcript controls (E2-090)

The saved viewport module provides a visually hidden focusable
latest-response heading before the composer. Its focus path calls an
abortable navigation callback and may focus a returned response target
without scrolling, or announce that no response is available. Tab-order
listeners adjust the heading's focusability. The conversation page imports
this control, exposes an atomic polite-live completion announcement that
tracks active request identity, and renders a busy page status during load.
Older-message pagination uses an IntersectionObserver on the scroll root
and a sentinel with either an accessible loading status or retry control.
These eight source-backed mechanisms are collected in the
[accessibility study](../specimens/chatgpt-com/v0002/chat_accessibility_trace.json).
No keyboard gesture, actual screen-reader speech, successful history fetch,
or accessibility audit was performed; the client source alone cannot prove
conformance or the accessibility of unmounted virtual rows.

## Capture-local module anchors for edit and accessibility evidence

Independent AST inspection of the private module registry resolved the edit
renderer to R-JS-069 module 12 and its page submit handler to R-JS-072
module 13. The latest-response focus landmark is R-JS-066 module 7 and the
older-message status component is R-JS-066 module 13; their import/consumer
sites are in R-JS-072 modules 13 and 30 respectively. The public reports
record only 1-based module ordinals, source resource references and reviewed
relationships, never source symbols, original filenames, or site code.
Module placement is valid for this exact saved capture only; it does not
verify a current deployment or runtime mount of the component.

## Full saved-bundle dependency census (E2-091)

The anonymous static module scanner was applied across every one of the
original 144 saved JavaScript bundles. It extracted 10,399 module-registry
entries and 51,285 unique literal import references: 50,714 resolved to
one saved module, 517 had ambiguous registry keys, and 54 had no saved
match. Of the resolved references, 36,330 cross bundle boundaries and
14,384 remain inside a bundle. Four curated links, identified only by
capture-local module ordinals, independently match the previously reviewed
conversation page/typed renderer, focus landmark, and older-history
loading paths. See the [module dependency report](../specimens/chatgpt-com/v0002/chat_module_dependency_trace.json).

The candidate graph is not a runtime trace: a module may be imported in
inactive code and never executed, and missing references may belong to
uncaptured or dynamically loaded assets. Source entrypoint investigation
is now active on the basis of this index. Current static queue: 12 active,
21 queued, none complete.

## Browser-local cache state and conditional snapshot-worker lifecycle

The saved JavaScript includes versioned browser-local conversation-list
metadata and pinned-list fallbacks, schema-checked reads and invalid-entry
removal, cached conversation lookups, query-client snapshot writes and
invalidation, plus an account-guarded optional local snapshot worker whose
cleanup can clear persisted snapshots. These mechanisms are documented in
[chat_persistence_cache_trace.json](../specimens/chatgpt-com/v0002/chat_persistence_cache_trace.json)
and canonical finding E2-092. Local storage-event handling observed in a
different subsystem does not establish **cross-tab conversation sync**.
Message-graph durability, actual writes and complete snapshot backing
storage remain unresolved. The associated static persistence task is now
in progress; the source queue is 13 in progress and 20 queued.

## Source CSS hook census and attribution limits

The captured page includes 17 CSS assets totalling 2,340,628 bytes.
A content-free lexical scan found 627 media rules, 504 container rules,
168 reduced-motion mentions, 493 focus-visible selectors, and numerous
state/role/test selectors. The literal CSS selector spellings of the
message-identity, message-role, source-message-ID and turn-key data
attributes from the JSX study occur zero times in captured CSS.
This **does not mean the transcript is unstyled**; the actual element
styles can use classes, variables or generated rules. The source study
[chat_css_hooks_trace.json](../specimens/chatgpt-com/v0002/chat_css_hooks_trace.json)
and evidence E2-093 document this boundary. The CSS hooks task is active,
with 14 static tasks in progress and 19 still queued.

## Composed end-to-end source lifecycle and proof types

The [saved client lifecycle trace](../specimens/chatgpt-com/v0002/chat_end_to_end_trace.json)
now connects ten stages: accepted composer submission, shared generation
dispatch, completion transport, decoded update classification, graph
mutation, scoped state commit, memoized turn derivation, presentation
mapping, virtual turn-window placement and typed DOM item rendering.
Each of nine links is labeled as a directly reviewed call, callback,
state-dependent composition, or component/derived-data relationship.
Five alternate paths cover regeneration, user editing, branch selection,
response cancellation and auxiliary browser caches, without attributing
backend durability to the client. Canonical evidence E2-094 opens the
architecture flow-review and chat feature transport/end-to-end tasks.
These remain **in progress**, not accepted complete: 17 active and 16
queued. Runtime observation is optional verification, not a prerequisite
for further static source study.

## Conditional completion recovery and retry defaults

The [transport failure trace](../specimens/chatgpt-com/v0002/chat_transport_failure_trace.json)
records the captured client's classification of HTTP, network and other
failures, a separate imported retryability predicate, delayed resumptions,
cancellation of obsolete resume requests, WebSocket topic handoff and an
independent initial-request refresh path. Captured fallback defaults include
up to 12 resume attempts, 300–5000 ms retry intervals with 1.5 backoff,
and separate WebSocket idle timeout settings; dynamic configuration may
override all these values. The source does **not** establish successful
recovery or current service-level guarantees. Canonical finding E2-095
anchors these observations to the active streaming, error and network
research without closing those tasks.
