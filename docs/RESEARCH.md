# Research protocol

## Definitions and stages

A **specimen** is a website identity controlled by a normalized site origin, a stable short slug, and an append-only series of **capture versions**. A version is an analysis of an individual saved-page snapshot, not the site's official release number. Captures may cover a single page, a multi-file saved page, or several pages in an archive. Scope is recorded, never assumed.

Stages: \`queued\` -> \`processed\` -> \`researching\` -> \`reviewed\`. Refresh produces another version. The specimen index tracks the latest version while every version remains available.

Local evidence is temporary input, not repository source. Process writes a private inventory to \`.work/<slug>/vNNNN/\` and public, empty research scaffolding to \`specimens/<slug>/vNNNN/\`. Version records and generated tasks start without findings; analysis must fill them. Do not confuse \`processed\` with \`fully analyzed\`.

## Capture-only evidence classes

- \`observed_static\`: directly established by saved files (for example the existence of a script reference in an HTML element).
- \`inferred_static\`: reasoned from saved implementation; conclusion is conditional on execution or environment.
- \`observed_live\`: independently reproduced live behavior, only if separate authorized testing actually occurred.
- \`external_source\`: secondary public documentation, cited with source and date.
- \`unknown\`: absent, underdetermined, excluded, or unobservable from provided materials.

Saved markup alone can support structure, DOM elements, visible metadata, resource paths, script/style inclusion, semantic markup, declared responsive breakpoints, and references to likely services. It cannot verify a remote API contract, server infrastructure, request outcomes, runtime execution, security of remote endpoints, or changes beyond the captured scope.

## Required research products

For each specimen version, produce a readable \`analysis.md\` and machine-readable \`record.json\` including:

- Scope, timestamp, capture limitations, previous version relationship.
- Site navigation and page structure.
- Scripts, imports, dependency clues and runtime responsibilities.
- CSS, layout rules, tokens, fonts, responsive styles.
- Images, icons and other asset categories; provenance and roles, never bundled content.
- Forms, controls, interactions, client state and local persistence clues.
- API/service references as hypotheses until observed.
- Accessibility, SEO/metadata, privacy/security considerations and performance clues.
- Cross-category architecture and dependency relationships.
- Open questions, evidence references and confidence bounds.
- Changes compared with earlier version: added, removed, altered, inconclusive due to scope.

Components are ontological units, not a verbatim file manifest. A record's \`evidence_ref\` is a locally meaningful research reference such as \`E-001\`; do not commit secret-bearing raw filenames or private paths. Sensitive mapping from identifiers to source bytes remains in the ignored local workspace.

## Queue semantics

Topical work queues live in \`queues/profiles.json\` and \`queues/tasks.json\`. Processing spawns the full initial work graph for that version. Stable IDs are \`<slug>-vNNNN-<topic>\`. Each task records dependencies and status: \`queued\`, \`in_progress\`, \`blocked\`, \`not_observable\`, or \`done\`. A dependency list describes sequencing, not a permission to invent answers. More specific follow-up tasks may be added manually with unique IDs and matching schemas.

Task profiles require honest closure. A static capture lacking sufficient evidence may still yield a completed analysis explicitly recording what remains unknown; \`not_observable\` marks a specific task outside the input's evidentiary reach. The overall specimen is not "complete" by simply exhausting generated tasks. Define scope-dependent completeness in the version dossier.

## Version changes

For every new capture, compare like-for-like evidence. Same-site evolution and differences in capture depth must be separated. Never overwrite a previous dossier or reset tasks from older versions. Site version \`v0002\` means the second processed snapshot here, not an official website version.

## Safe publication

Raw captures and private inventories are never committed. Do not place screenshots or third-party assets in the gallery without explicit provenance, license and publication clearance. Read each proposed technical identifier and quotation for data leakage. Public-only descriptions should be original and minimal. Automated redaction cannot establish the right to publish third-party content.

## Closing the scope of a single saved-page capture

Complete a source-limited task when the available saved markup and included source have been analyzed and the resulting limitations are recorded in the version dossier. Use `not_observable` for tasks whose essential outcome requires absent source, runtime behavior, a previous snapshot, or unavailable external evidence. A reviewed version and fully resolved task queue means the **available evidence was exhausted**, not that the full website was reconstructed. Preserve all unknowns for a subsequent numbered capture.

When possible, add a sanitized `resource_inventory.json` with category-local ordinals for every external HTML resource reference, excluding raw filenames, URLs, code and other private capture data. Ordinals are not stable cross-capture identities. The machine record may include corresponding typed components. Raw capture content and confidential local evidence remain untracked.

## Feature-level behavioral research

For a feature such as chat interaction, keep the **observed interface** separate from a **candidate state machine**. First record the visible controls and their version-scoped ontology references, then map proposed events, states and transitions. Each graph transition must list guards, anticipated effects, evidence status, and a specific verification experiment. Never interpret an unobserved state edge as a recovered product API.

Use synthetic, disposable test cases if the owner separately authorizes live tests. Collect only structural deltas (for example an abstract selected-chat state), timing and generic event categories. Do not extract real conversation IDs, session values, message text, request payloads, network endpoints or browser profiles into the public repository. A reviewed static snapshot may have a candidate feature graph with unverified transitions; future observations belong to separately sourced evidence and versioned research.

## Automatic source-level research on every dump

Any processed site dump containing JavaScript now queues implementation-level
tasks, **even when it is a small ZIP or a standalone page with inline script**.
The separate `queues/static_profiles.json` contract enumerates required
work on functions, call chains, object shapes, UI handlers, state flows,
requests/decoders, streaming, retries, persistence, render connections, and
evidence reconciliation. CSS captures additionally queue style-hook tracing.
Large-archive deep-profile tasks remain in force independently.

Fixed, curated lexical markers in captured JavaScript may also enqueue
candidate feature investigations (chat, search, authentication, commerce,
media playback, maps, document editing), four detailed tasks per detected
feature. Co-occurring words only **trigger questions**; they never constitute
verified feature behavior. Feature signal matches and raw file references stay
in the ignored private inventory. A site not matching the predefined
vocabulary still receives the general source function and end-to-end research
tasks. All tasks stay queued until actual source-level evidence is reviewed;
no task is automatically closed by a frequency census.

The requirement is to reconstruct real captured client implementation before
declaring static analysis exhausted. Runtime authorization is not required to
study the downloaded JavaScript. Only claims that source cannot establish,
such as actual server responses or account-specific execution, remain unknown.

## Requeueing existing captures after improved research profiles

When a new static research profile becomes available after an earlier
review, run `python3 scripts/viewsource.py enqueue-static <slug> --input
/path/to/original.zip`. It does **not** invent a new snapshot version or
replace captured evidence. It checks the private original capture digest
when available; for older reviewed snapshots with no retained private
inventory, it requires compatibility with the published aggregate resource
census. It creates only missing tasks and is idempotent.

A previously reviewed current snapshot re-enters `researching` status
when unfinished static implementation work is added, while the original
findings and terminal task dispositions remain intact. This is a research
scope extension, not a claim that older reviewed evidence was invalid.

## Offline AST tracing

`scripts/trace_static_archive.py` can inspect the captured scripts in a private temporary directory using `scripts/static_ast_probe.cjs`, which requires the small Acorn development dependency. It walks function scopes, records allowlisted literal field operations and field assignments, and emits only aggregate candidate counts. Parsing performs **no evaluation**. Module/file names, source spans, string values, real request paths, and captured code never enter the report. Function co-occurrence is only a starting point for the new source-level queue; function ownership and calls still require evidence-based tracing, and no runtime claims can be promoted from this probe.

## Candidate selected-ancestry and UI selector scanning

Use `python3 scripts/trace_static_archive.py --input /path/to/private-capture.zip --selector-trace` for a content-free AST scan of captured JavaScript. This mode recognizes separate **candidate** categories for root-to-selected message traversal, user-authored ancestry IDs, automation-reference extraction, and recent-turn control code. The common private ZIP bridge supplies capture-local resource ordinals and never runs downloaded code. It is available alongside `--chat-trace` and `--transport-trace`; only one specialized mode may be used at a time.

The implementation intentionally distinguishes actual selected-message ancestor walks from feature-reference extraction. An ancestry walk alone cannot identify the React component that consumes it. Candidate classifications require source/module export tracing and manual verification before a canonical finding is added. An independent fictional ZIP regression checks the reporting boundary, and the new parser has its own synthetic AST self-test in GitHub Actions.

## Capture-driven transcript implementation candidates

The optional offline `--transcript-trace` archive mode runs
`scripts/trace_transcript_impl.cjs` to find six **candidate** AST patterns:
render-turn derivation, pending-turn preparation, first-user-item display
filtering, typed turn rendering, DOM message identity wrappers, and
alternate selected-message derivation. It emits only resource/function
ordinals and fixed pattern labels. Function lexical scans include nested
callback properties, so an individual hit does **not** prove ownership,
execution, or a complete call path. These leads inform the automatically
queued source-rendering tasks for each new dump; manual cross-module call
review and explicit evidence limitations are still required before an
observed-static finding is created. The test suite uses synthetic inputs
only and never commits captured JavaScript.

The transcript candidate probe also distinguishes response-version navigation
controls (previous/next variant indexing) from the persistence request
construction for a selected current node. These separate lexical candidate
categories do not establish successful server acknowledgement or a current
public protocol. Captured client branch-switch semantics are reviewed in
`chat_branch_switch_trace.json`, not inferred solely from this scanner.

One further candidate pattern, `eligible_variant_derivation`, looks for
source functions that distinguish raw response-child count, filtered
variant identities and the selected variant index. It is **not** equivalent
to finding a user-visible version switcher. Verified client behavior belongs
in the branch-switch study, while this detection only adds an inspectable
static lead for new site captures.

## Virtual list and scroll anchor investigation

The specialized offline mode `--viewport-trace` reads captured JavaScript
from a private ZIP, parses source module ASTs, and reports only fixed
category labels and numeric source/module ordinals. Its categories include
measured/estimated layout, overscan range computation, retained rows,
viewport resize, scroll anchoring, targeted turn restore, response spacer,
manual input cancellation and history boundary signals. The scanner
handles both bundled registries and standalone JavaScript modules. As with
other source detectors, module-wide co-occurrence is **candidate evidence**,
not proof of ownership, execution or UI behavior; independently inspect
candidate source before publishing implementation conclusions.

The first reviewed example is the captured chat virtualizer: R-JS-066
module ordinals 9 and 14 and R-JS-072 ordinals 13 and 14. The public
report and tests identify these modules only by capture-local ordinals,
never by original minified identifiers or raw proprietary source. See
E2-084 and the standalone viewport study. Actual browser measurements,
React reconciliation and live accessibility outcomes remain outside
static proof.

## Intake contract: render ownership includes viewport mechanics

The automatically enqueued `source-render-bindings` investigation now
explicitly checks **typed item dispatch, virtualization, scroll anchoring,
retained rows and restore behavior** when captured source contains them.
Where no such code exists, document the evidence gap rather than
inventing functionality. The `--viewport-trace` AST mode is a focused
research instrument available to the queued worker; its fixed labels and
module ordinals can direct source review but cannot close a task by
vocabulary counts alone. No runtime access is required to investigate
the saved client scripts.

The same transcript AST candidate scan now recognizes bounded Markdown
selection range guards and code-block copy recovery paths with AbortController
cancellation. These are **candidate** syntax signals, not independently
verified user actions. The saved ChatGPT capture's reviewed interpretation
is separately documented in the selection/copy study (E2-087 and E2-088).
A synthetic ZIP test exercises these two candidate classes without exposing
source literals, user text, file names or account data.

## Anonymous bundled-JavaScript import graph

Use `python3 scripts/trace_static_archive.py --input /private/capture.zip
--module-trace` to inventory bundled module tables and literal static
import candidates by capture-local resource and 1-based module ordinal. The
module registry's original keys are joined **only in temporary memory** and
are never included in the returned JSON. Unique references are represented
as ordinal-to-ordinal links; missing and ambiguous keys are counted without
guessing a destination. This creates a reusable investigation graph for
future site dumps without executing JavaScript or publishing source.

The graph is an **AST candidate index**. An import can be conditional, unused,
or hidden behind an inactive feature. Module links do not establish that a
user loaded a feature or that its server contract is valid. A two-bundle
synthetic ZIP test checks cross-bundle resolution and the absence of private
module identifiers in the result. Existing source investigations remain
queued automatically and can use this graph as a dependency-discovery input.
