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

## Repeatable CSS and JS hook candidates for new captures

`python3 scripts/trace_static_archive.py --input /path/to/capture.zip --styles-trace`
scans private, temporary copies of captured stylesheets and JavaScript
without executing either. The tool emits only aggregate counts for
`@media`, `@container`, reduced-motion/focus rules, allowlisted state/role
attribute selectors, exact message-attribution attribute-selector gaps and
limited shared thread-content wording between scripts and stylesheets.
These are **lexical counts**, not a computed CSS cascade, matched DOM style,
or assertion that any named component is unstyled. The source-specific
study and acceptance evidence must still link actual component class/state
tokens to reviewed style rules. CI uses an invented ZIP and a synthetic
JavaScript self-test; the real specimen CSS is never committed.

## Ambiguous module IDs: export-shape candidates

The private ZIP's `--module-trace` analyzer now retains an anonymous
export-shape candidate layer alongside its existing conservative registry
census. When a short module key resolves to multiple captured definitions,
it compares statically referenced property slots on an imported module
alias with the available export slots on each definition. A uniquely
matching interface yields an **anonymous candidate source/target ordinal
pair**, not a verified module load or runtime execution. The original
ambiguous-import total remains unchanged. Reused aliases, lexical
shadowing, dead code and dynamic access may create false leads; reviewers
must inspect call sites before promoting candidates to canonical findings.

The ChatGPT completion-resume study supplies an individually reviewed case:
R-JS-018 imports a three-role recovery interface, and only R-JS-004
matches that required interface among two duplicate registry definitions.
That case is documented in `chat_module_dependency_trace.json` and
`chat_transport_failure_trace.json`. The general-purpose parser's
synthetic tests intentionally include a colliding-key fixture and verify
that no private module name or source is published.

## Feature-specific AST leads (offline)

Use `python3 scripts/trace_static_archive.py --input /private/capture.zip --feature-trace` to classify candidate search, authentication, media-playback and document-editing functions. The Acorn parser reads ordinal-only temporary copies of captured JavaScript and emits fixed pattern names, source/function/parent ordinals and aggregate counts. It never executes captured assets. Pattern matches require limited member/property co-occurrence inside one function body, which is stronger than archive-wide lexical counting but **does not establish control ownership, true dataflow, an executed feature or a backend contract**. The 16 queued feature tasks remain queued until researchers trace actual modules, calls, state and UI. Synthetic ZIP regression tests require private strings and file names to remain absent from reports.

## Seeded module import frontier

After producing a private ordinal-only module report with `--module-trace`, use
`node scripts/trace_module_frontier.cjs --input /private/module-report.json --root R-JS-072:13 --max-depth 6`
to inspect imports reachable from a **manually reviewed** capture-local module. Several
`--root` values can be supplied. The tool uses saved import edges exclusively and
does not read or execute captured JavaScript. Its bounded traversal is useful for
prioritizing unresolved imports and review of module dependencies. It deliberately
does not traverse ambiguous export-shape candidates; they are reported separately.
The resulting hierarchy is a **candidate static dependency frontier**, not evidence
that a bundle was bootstrapped, loaded by the browser or executed in a chat session.
Keep private analysis reports outside Git; only publish original conclusions after
manual examination and release review.

## Conservative module bootstrap candidates

The ordinal-only `--module-trace` report also detects a narrow
startup pattern: a literal module-key request through
`__webpack_require__` in top-level expressions or an immediately invoked
function. Matches are resolved against the captured registry in temporary
memory and only anonymous module ordinals, duplicate-key status and counts
are returned. Calls in declarations and callbacks not immediately invoked
are excluded. Other bundler initializers, aliased/minified require functions,
dynamically calculated keys, loading policy and script execution are
**not** captured by this probe. A candidate therefore offers a starting
module for manually seeded frontier analysis, never proof of startup or
browser module execution. Private module keys, filenames and source remain
unpublished.

### Bootstrap-seeded dependency frontier

Run `node scripts/trace_module_frontier.cjs --input /private/module-report.json --bootstrap-candidates --max-depth 6`
to seed a bounded import walk from **uniquely matched static bootstrap-call candidates**.
Unlike `--root R-JS-072:13`, this does not require an individually selected
source module. Ambiguous or missing bootstrap keys are deliberately excluded,
and the output explicitly records `root_source=bootstrap_syntax_candidate`.
Neither the bootstrap pattern nor any reachable import is verified to have run.
A report without a unique seed is rejected rather than fabricating one.

### Static dynamic-import boundaries

The same private `--module-trace` pass records four fixed AST lead categories
on captured module factories: literal `import()`, computed `import()`, and
recognized bundler chunk-loader calls. It reports only capture-local resource and
module ordinals and fixed category names. Imported strings, chunk IDs and source
spelling are suppressed. None of these leads is traversed as a resolved module
import, since chunk resolution and runtime feature activation require further
source review. An absent match is not evidence that the application has no lazy
loading: this parser only recognizes the supported syntax.

### Unresolved boundaries in dependency frontiers

The module frontier report includes dynamic-loading AST categories attached to
already reachable module ordinals. This allows reviewers to spot areas where a
literal-import-only traversal may be incomplete. Dynamic boundaries **do not**
expand the traversal or imply the target bundle exists in the saved archive.
The report shows them separately from ambiguous export-shape candidates and
uses the same closed, source-limited evidence policy.

### One-step ZIP-to-frontier research

To avoid manually copying intermediate reports, the private ZIP bridge now supports
`--module-frontier`:

`python3 scripts/trace_static_archive.py --input /private/capture.zip --module-frontier --bootstrap-candidates --max-depth 6`

Alternatively pass one or more `--root R-JS-072:13` values instead of
`--bootstrap-candidates`. The bridge runs the module scanner and passes
the ordinal-only report through standard input to the bounded frontier tool;
no intermediate report file is created and no captured assets or source strings
are emitted. Both stages only parse private files without executing captured code.
The resulting frontend is a candidate static dependency graph, **not** proof of
module activation, page entrypoints or a live client trace.

### Lexically scoped import alias inference

The export-interface candidate matcher resolves imported alias properties within
the lexical block and function scope that declares the alias. Distinct functions
reusing an identifier spelling do not contribute each other's required exports.
Reassigned or unrecognized bindings are treated conservatively. This reduces
false disambiguation of duplicate minified module keys, but does not turn a
candidate into a reviewed call edge or prove runtime execution.

### Bound module-loader callbacks

A captured module factory may bind its loader to a literal target key for
future use. The module analyzer records a conservative loader-bound-call
signature and emits only anonymous source/module ordinals with a
unique/ambiguous/missing target classification. Such callbacks never count as
direct imports or verified module loads. Invocation and ownership must be
established independently before promoting the candidate to a source finding.

### Module-loader shadowing

The direct-import, bound-loader and export-interface candidate passes now
distinguish the actual bundled module-factory loader parameter from a nested
function argument that merely reuses the same name. A shadowed parameter must
not create a candidate dependency on the factory loader. This rejects false
static edges in minified code but cannot prove that any accepted edge executed.

### Scoped export inference and ambiguous short module IDs

A duplicate module registry key can be disambiguated by its required export
slots only as an unverified lead. Export inference now excludes assignments
and helper registrations that refer to a shadowed or reassigned factory export
parameter, and ignores nonliteral computed export keys. A unique candidate
does not change ambiguity counters or become evidence of module execution.

### Computed bundled module keys

The ordinal-only module probe now reports a separate
`computed_module_require_candidate` boundary for a factory loader invoked
with a nonliteral key. Calls through unrelated shadowed parameters are
excluded. No string representation of the key or its source expression is
emitted, and computed keys never count as uniquely resolved dependency
edges. The dependency-frontier report exposes the category only at reached
module ordinals.

### Numeric module registry keys

Literal webpack module identifiers can be strings or nonnegative safe
integers. The module analyzer now normalizes integer keys internally for
direct imports, bootstrap candidates, export-shape matching and bound
loader callbacks. Numeric keys never enter public reports: only
capture-local resource/module ordinals and aggregate classifications
are emitted. Computed expressions remain unresolved boundaries.

### Bounded dependency review paths

Each reached module in a private frontier report carries its first
breadth-first predecessor and the `static_import_candidate` edge
classification. Roots have no predecessor. The `boundary_details` list
now distinguishes depth-limit and node-limit truncation, and omits a
depth-limit boundary when every outgoing edge already returns to a
reached module. Paths are static candidates only, **not** executed call
stacks, request paths or proven runtime import chains.

### Strict ordinal graph validation

Before showing a private frontier, the reader checks count fields as bounded
nonnegative integers, reconciles the module census and verifies that supplied
candidate-count fields match their arrays. It also reconciles the direct
import partition when present. A malformed graph is rejected without echoing
the input, preventing private strings from being copied into an ostensibly
sanitized numeric summary. This check validates consistency, not evidence
that candidate imports ran.

### Ordinary top-level webpack module tables

The anonymous module parser accepts both ordinary top-level `var`,
`let` or `const __webpack_modules__ = {...}` declarations and
equivalent exported declarations. This improves static registry coverage,
but only the recognized syntax contributes to candidate dependency counts.
Other bundler formats remain outside the recognition boundary until
independently reviewed. The parser does not execute registered factories.

### Bundler chunk registration tables

The anonymous dependency scanner recognizes a narrowly scoped Webpack
chunk registration expression: `self`, `window` or `globalThis` property
starting with `webpackChunk`, followed by `.push([chunk_ids, module_table])`.
It reads only object-literal module-factory entries and does not publish
private chunk names, IDs or implementations. This detects possible
source modules in saved lazy-loading bundles, not an observed network
download, active chunk or executed module.

### Isolated Webpack runtime namespaces

Two unrelated Webpack runtimes can reuse the same numeric or string module
registry key. The offline module dependency scanner now keeps recognized
`webpackChunk*` registrations in their **own capture-local namespace**.
Registrations sharing the same chunk global are eligible for cross-bundle
static import matching, even if the global is referenced through different
window-global aliases. Distinct chunk globals cannot supply one another's
module target or disambiguate an export interface. Private names remain only
in transient memory and **never** enter ordinal reports or the public atlas.

An ordinary `__webpack_modules__` table has no provable named runtime in
this scanner, so those entries form an explicitly provisional unscoped group,
separate from named chunk registrations. Neither a shared chunk name nor a
unique module key proves that the browser executed a module. The emitted
`registry_runtime_scope_count` counts in-memory resolution partitions,
not confirmed independent running runtimes.

### Unresolved imports with foreign-registry key collisions

An import can remain unresolved in its own Webpack chunk namespace even when
a module with the same key appears in a **different** namespace. Such cases are
reported separately as `foreign_registry_key_collision` diagnostics with
only the importing module's capture-local ordinal and the number of foreign
definitions. The cross-runtime definition is **not** emitted as a target,
and frontiers do not traverse these cases. The unresolved-import total
continues to include them; the diagnostic count is a subset, not a
new category of resolved imports.

### Catch-parameter lexical shadowing

AST import and export scans now treat a `catch (binding)` parameter as
a local lexical binding instead of an inherited factory loader, export
parameter or imported-module alias. A catch block cannot create an import
edge, bound-loader callback or export-interface signature through a
shadowed name. The test suite includes duplicate-key ambiguity and
source-nonpublication regressions. These are conservative static candidates
and do not imply execution.

### Explicit offline JavaScript parse coverage

The ZIP-to-module scanner distinguishes the number of candidate JavaScript
resources, the number excluded for the per-script size limit, the number sent
to the parser, and the number that failed parsing. Failed parse resource
references are expressed solely as capture-local `R-JS-NNN` ordinals; source
paths, error details, and raw code are never returned. Both `--module-trace`
and `--module-frontier` report `archive_all_scripts_parsed`, which is
**false** whenever any script was skipped or failed parsing. The frontier
validates these counts before returning the bounded dependency report.
Even when all captured JavaScript parses, the scanner's selective syntax
recognition **does not** establish that every feature was analyzed.

### Candidate entrypoints in Webpack chunk runtime callbacks

Some saved chunks include a third-position runtime callback alongside a
chunk-ID vector and a module table. The module scanner recognizes only a
literal direct call or return call to the callback's first parameter.
If that module key is uniquely present in the **same private chunk namespace**,
the report includes a `chunk_runtime_literal_call_candidate` bootstrap lead.
That candidate can seed `--module-frontier --bootstrap-candidates`. Deferred
nested callbacks, conditional branches and computed targets do not qualify.
Chunk registration and static callback source are not proof of runtime
invocation, network requests or actual module activation.

### Provenance of proposed bootstrap roots

When a frontier is automatically seeded from candidate startup syntax, the
result includes `bootstrap_root_provenance` with fixed category names,
the number of matching static calls and an explicit `execution_verified:
false` guard. Recognized categories distinguish direct top-level loader
calls from third-position Webpack chunk runtime callbacks. A proposed
bootstrap root must actually appear among the input candidate records;
an arbitrary ordinal cannot be mislabeled as an observed entrypoint.

### Root-local unresolved module import questions

The module graph now retains anonymous per-callsite records for missing and
ambiguous literal module imports. Each record includes only its importing
resource/module ordinal, a fixed classification, the number of same-registry
target definitions and `import_resolved: false`. No source identifier, key,
specifier or captured text is emitted. The frontier filters these records
to **reached modules** and reports a `reachable_unresolved_import_count`
separately from global unresolved totals. This makes source-review questions
relevant to the selected dependency path, without implying any missing
module was requested in a running browser.

### Loop and switch lexical scopes

Candidate import, alias-property and export scans now keep `for`, `for...of`,
`for...in`, and `switch` declarations in a dedicated conservative scope.
Bindings local to those control-flow structures no longer overwrite aliases
in the surrounding module factory. This prevents local shadows from
creating false import edges or hiding legitimate later alias-property
reads. Branch control flow and actual execution remain unverified.

### Direct function-valued export assignment leads

The offline AST module scanner now inventories functions **directly
assigned** to a recognized module factory's export object, such as
`exports.handler = function () {...}` or an arrow-function assignment.
Each published analysis record is only a source reference, module ordinal,
function-export ordinal and fixed candidate classification. Getter exports
that wrap other values, aliases and shadowed export parameters are not
promoted to verified function ownership. The dependency frontier exposes
only candidates associated with reached modules; neither an exported
function's invocation nor ownership of a user-visible feature is established.

### Mutable runtime callback loader parameters

A direct literal call in a Webpack chunk runtime callback is no longer
considered an entrypoint lead after an earlier statement could reassign or
update the callback's loader parameter. Conditional rebinding is treated
conservatively: the analyzer does not prove the branch was taken, so the
subsequent call is excluded rather than mistaken for a loader invocation.
An earlier direct call can still be reported. Nested function assignments
are not treated as preceding execution, and no captured code is run.

### Whole-module callable assignments

When a module factory assigns a function expression directly to its
first parameter's `exports` property (for example
`module.exports = function () {}`), the analyzer records a
`module_object_function_assignment_candidate`. It remains distinct
from an `exports.handler = () => {}` function-valued property
assignment. Shadowed nested `module` parameters are excluded.
Neither category establishes that the exported callable was invoked,
or that its enclosing module belongs to a specific UI feature.

### Deterministic dependency-frontier order

The private frontier reader sorts unique source/module root ordinals and
the outgoing static-import candidate targets before breadth-first
exploration. Predecessor paths, output node order and node-limit
truncation therefore no longer depend on input JSON edge order or the
order in which roots were supplied. This improves reproducible review;
it does not imply a browser's import or execution order.

### Distinct module imports versus repeated literal call syntax

Module dependency reports distinguish *distinct literal module keys
referenced per module factory* (`import_candidates`) from the number
of literal factory-loader call expressions found in captured source,
including repeated references to the same key. Root-local frontier
reports include the latter count only for reached modules. Both are
AST-source metrics, not executed call counts, feature invocation
frequencies or observed network requests.

### Inherited bindings after conditional assignments

A conditional block, loop, catch, or switch can change an inherited
module loader, export object, or imported alias. The static scanner
now marks these outer identities as uncertain after a potential
assignment, including when the branch might never execute. A locally
declared shadow instead remains local and does not invalidate the
outer binding. Nested function declarations are kept separate because
their invocation is not established by the saved source. This improves
the conservative classification of post-branch imports and exports
without claiming runtime execution.

### Non-callable entries in captured module tables

A literal module-table property is not necessarily a callable factory.
The analyzer retains its ordinal in the capture-local census but does
not resolve a literal require to that property unless its value is
a function or arrow-function factory. A callable with fewer than
three parameters remains a valid potential target even though it
cannot itself be scanned for factory-loader calls. The
registry_nonfactory_entry_count field describes static source
coverage, not proof of any runtime module load.

### Imported-object property writes are not required exported slots

The export-interface disambiguation pass now excludes imported-object
assignment targets, increment/decrement targets and delete operands from
the set of required exported properties. Writing to an object obtained from
a module loader is not evidence that the original module exported that
property. Actual member reads and calls remain syntax candidates. These
restrictions reduce false unique matches when multiple saved registries
reuse a module key; they do not establish runtime module identity.

### Assignment targets in loops and destructuring

Required export-interface slot inference also omits imported-object
properties on the left side of `for...of`, `for...in`, and
destructuring assignments. These are write targets, not evidence
that the imported module originally defined those properties.
The AST analyzer deliberately prefers an unresolved candidate
over an incorrect unique registry-key match.

### Computed nonliteral registry keys

A registry object property keyed by a runtime expression, such as
a computed identifier, must not be mistaken for a literal module ID.
The analyzer preserves such callable factories under their anonymous
source/module ordinals, counts them as unresolved computed registry
keys, and still scans their internal candidate imports. It will not
use the computed key's source spelling to resolve an import.
String and integer literal computed keys remain valid registry IDs.
An unresolved property-key expression provides no observed runtime ID.

### Loader call syntax inside nested functions

The scanner now reports the subset of literal loader-call expressions
written inside nested functions or arrow callbacks of a module
factory, separately from the total literal-call expression count
and distinct imported-module keys. Root-local frontiers include the
nested count only for reached module ordinals. This identifies a
review priority for conditional or callback import paths without
assuming they execute later: immediately invoked nested functions
can still run synchronously. The scanner does not execute the code.

### Chunk loader rebinding versus lexical shadows

Entrypoint-candidate detection now distinguishes a potential mutation
of the outer runtime-loader parameter from a block-local declaration
with the same spelling. Lexically scoped let/const and catch bindings
do not invalidate a later call through the original parameter.
An initialized var declaration remains a possible mutation of
the enclosing function parameter. Neither syntax result proves
a chunk runtime callback actually executed.

### Function-scoped var in static module analysis

Module loader, imported-alias, and export-object tracking now separates
function-scoped `var` declarations from block-scoped `let` and `const`.
An initialized `var` inside a block can invalidate an outer loader or
export parameter, while a bare `var` redeclaration does not by itself
replace a function parameter. For-in/of declarations using `var`
may assign the function-scoped binding, so later imports remain
conservatively unresolved. Nested function bodies hoist their own
`var` declarations to avoid accidental matches against the factory
parameter they close over. Synthetic ZIP regressions cover these cases.

### Runtime callback loader writes through assignment patterns

The Webpack chunk-runtime entrypoint detector excludes direct-looking
literal startup calls after a possible mutation of the callback loader
through `for...of` or `for...in` iteration targets, including
function-scoped `var`, or through destructuring assignment patterns.
A block-local `let` or `const` with the same identifier remains
separate. This distinction prevents false entrypoint claims; it does
not verify whether the runtime callback or any mutation ran.

### Bounded static candidate inventories

Private module analysis limits both the module census and the
high-cardinality diagnostic arrays. Distinct import candidates,
bound loader callbacks, function-valued export assignments,
dynamic-loading syntax leads, and startup-call candidates cannot
grow beyond the fixed candidate budget. The scanner fails closed
with a generic error rather than emitting a partial graph or
captured source when a limit is exceeded. This is a resource
safety bound, not a claim that a truncated capture has been
fully analyzed.

### Detached CommonJS export aliases

The scanner distinguishes assignments through the factory's original
`exports` parameter from replacement of `module.exports`. After
a whole-module replacement, the original `exports` alias can refer
to the previous object; neither earlier nor later property writes
through that alias establish the final public export interface.
The conservative analyzer drops those candidate export slots and
function-valued property assignments, while retaining a direct
whole-module callable assignment if its right-hand side is a function.
This prevents an obsolete alias from falsely disambiguating duplicate
module keys; execution and final runtime ownership remain unverified.

### Scope-aware top-level startup leads

A literal `__webpack_require__(key)` call is only a candidate bootstrap
when the referenced identifier still denotes the presumed top-level
loader. The scanner now conservatively invalidates that identity after
possible reassignment and does not count calls made through locally
shadowed bindings, including immediate-function parameters and block
declarations. A directly invoked wrapper without such a shadow may
still supply a static lead. Deferred function bodies do not qualify.
These are syntax classifications, not observed browser startup events.

### Candidate-evidence consistency checks

Before producing an ordinal-only frontier, the private graph reader
validates the available bootstrap and bound-import definition counts
against their classifications: unique targets must have one definition,
ambiguous targets at least two, and missing targets zero. Direct
function-export candidates for the same module must use consecutive
one-based ordinals. Contradictory evidence is rejected rather than
converted into an apparently valid frontier. The reader accepts older
candidate records without optional definition-count fields for
compatibility; no validation implies observed runtime execution.
