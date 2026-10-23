# Viewsource

Viewsource is an independent public research repository for studying how websites are built and how their observable interfaces behave. Websites are **specimens**, not dependencies or copied codebases. Each specimen has versioned, evidence-aware, human-readable and machine-readable documentation.

A single downloaded HTML page or ZIP of saved-page files is a sufficient input for initial analysis. Live access, a browser session, cookies, privileged APIs, and full backend visibility are **not required**. Observations unavailable from the supplied capture remain explicitly unknown.

## Core boundaries

- **Do not commit input captures.** No supplied ZIPs, HTML copies, JavaScript bundles, stylesheets, network archives, media exports, screenshots, caches, browser profiles, or extracted trees from specimens belong in this repository.
- Work with supplied files only in an ignored local workspace. Analyze them, then publish original, concise, cleared findings and structured descriptions; never republish third-party site implementation or captured page contents.
- The public repository stores project code, schemas, work queues, versioned specimen analysis, and a gallery of separately cleared work only.
- Protect credentials, identifying content, session tokens, private URLs, local paths, proprietary content, and material with unclear publication rights.
- Distinguish facts directly visible in the saved files, reasonable deductions, and unknown behavior. Never invent live or server-side details from a static capture.
- Keep this project independent of unpublished systems. Its Tarium central-registry membership requires a **separate, explicit owner instruction**; see [CONSTITUTION.md](CONSTITUTION.md).

## Workflow

1. **Queue** a site using a simple domain or origin. A site is a persistent specimen identity.
2. **Process** a local saved-page ZIP or a standalone HTML file. The intake tool inventories it without unpacking into Git, creates the next internal specimen version, and spawns a task graph across topical queues.
3. **Research** the local inventory and source files. Every claim is supported by a capture observation, an explicitly labeled inference, or is recorded as unknown.
4. **Publish** a technical description, version record, and machine-readable component/relationship ontology. Separately approve any gallery entries.
5. **Refresh** the specimen on another capture; retain older versions and identify supported changes rather than overwriting past conclusions.

From repository root (Python 3.10+, standard library only):

~~~sh
python3 scripts/viewsource.py queue example --origin https://example.org
python3 scripts/viewsource.py process example --input /path/to/saved-page.zip
python3 scripts/viewsource.py status
python3 scripts/work_queue.py ready --specimen example
python3 scripts/static_census.py --slug example --version 1 --input /path/to/saved-page.zip
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
~~~

The intake input path must point **outside** the repository. It is read only. For an HTML file, the same `--input` flag is used. Private inventory output is placed under ignored `.work/`; only controlled templates and task metadata are written to tracked paths. Review all generated public changes before pushing; automatic generation is not a publication-rights determination. `process` does not execute site scripts or request any network resources.

## Repository map

| Path | Role |
| --- | --- |
| [CONSTITUTION.md](CONSTITUTION.md), [AGENTS.md](AGENTS.md) | Mandatory publishing and research rules |
| [ontology/](ontology/README.md) | Project-level ontology: terms, relationships, semantics, evidence classes |
| [schemas/](schemas/) | JSON schemas for version records and tasks |
| [specimens/](specimens/README.md) | Approved research dossiers and immutable numbered versions |
| [queues/](queues/README.md) | Task profiles and open research items |
| [gallery/](gallery/README.md) | Human-readable gallery and machine-readable index |
| [docs/](docs/RESEARCH.md) | Research, evidence, limitations, and versioning procedures |
| [scripts/](scripts/) | Offline intake and validation |
| [tarium.json](tarium.json) | Independent public-project resource manifest |

See [static census](docs/STATIC-CENSUS.md) for a private, content-free structural summary and [queue guide](queues/README.md) for dependency-aware work scheduling.

## Specimen Atlas website

**Website:** https://sguzman.github.io/viewsource/

The public, privacy-bounded research website lives in [site/](site/) and is built with [scripts/build_site.py](scripts/build_site.py). It turns curated findings, ontology relationships and persistent task queues into an accessible, searchable specimen narrative with an evidence inspector and interactive component graph.

The **Appearance** dropdown provides **System** (default), **Light**, and **Dark** modes. Its selected preference is stored locally in the viewing browser. No captured source is executed by the atlas.

A large ZIP now automatically generates **57 additional dependency-linked deep research tasks** (when matching source categories are available), beyond the standard 18-task intake phase; these are **queued** until substantively completed with evidence. ChatGPT v0002 has completed its offline deep research audit: 37 deep tasks supported by static findings, and twenty explicitly not observable from this ZIP.

Run `python3 scripts/build_site.py --out _site` to generate the static site locally. The GitHub Pages workflow builds the same self-contained artifact from public repository data without storing private captures.

## What analysis covers

Structure, routes and navigation; scripts and module loading; script responsibilities; CSS and design tokens; assets, fonts and media; accessibility and semantics; forms and interaction; client state and persistence; third-party services; requests and APIs suggested by static references; build signatures; performance hypotheses; privacy and security indicators; metadata and search discoverability; responsive behavior; dependency relationships; and differences between snapshots.

These are research **queues**, not automatic guarantees of complete observation. An accurate unresolved item is preferable to an invented explanation.

## Current contents

**One website specimen, now with two snapshot versions:** [chatgpt.com v0001](specimens/chatgpt-com/v0001/analysis.md), with a [machine-readable ontology record](specimens/chatgpt-com/v0001/record.json), [31-entry sanitized resource inventory](specimens/chatgpt-com/v0001/resource_inventory.json), and [gallery entry](gallery/README.md). The first-capture task graph has 14 completed and four unobservable tasks. The [v0002 ZIP study](specimens/chatgpt-com/v0002/analysis.md) adds deep static research of 234 captured resources, a [candidate source-reference graph](specimens/chatgpt-com/v0002/source_analysis.json), a [detailed static analysis](specimens/chatgpt-com/v0002/deep_analysis.json), and a reviewed task graph. Both versions are source-limited and are not claims of whole-site runtime coverage.

[chatgpt.com v0002](specimens/chatgpt-com/v0002/analysis.md) expands the research to 234 captured resources (144 JS, 17 CSS, 60 fonts, 12 images, one additional HTML file). Its [privacy-safe resource index](specimens/chatgpt-com/v0002/resource_inventory.json) and [machine-readable ontology](specimens/chatgpt-com/v0002/record.json) are published with final offline research dispositions recorded in the [task queues](queues/tasks.json) and a [source-level system report](specimens/chatgpt-com/v0002/phase5_system_analysis.json). v0001 remains separately reviewed and intact.

## License

Project-owned code and documentation are available under [MIT](LICENSE). This license does **not** grant rights to any third-party website material submitted for private analysis.

**Prior audit scope:** v0002's original phases completed 69 tasks and classified 22 as unobservable. That audit is preserved, but the same captured assets have been reopened for **33 automatically defined source-level implementation research tasks**. The current snapshot status is researching, not fully analyzed.

## Chat interaction research

The original v0002 archive audit was completed, but the specimen is now **researching** while deeper static JavaScript implementation analysis continues. Chat behavior is not yet fully reconstructed. The [chat-specific source evidence](specimens/chatgpt-com/v0002/chat_source_signals.json) describes what the saved JavaScript and DOM can support without publishing any source content. The [feature interaction graph](specimens/chatgpt-com/v0002/chat-interaction.graph.json) provides typed message and conversation entities, candidate state machines and transitions, and explicit verification steps. Its edges are hypotheses, not a working internal API map.

The independent [chat feature backlog](queues/chat_research.json) tracks **10 completed earlier tasks and 8 optional runtime verification questions**; those questions do not block further static-source analysis. Source analysis, graph tooling and strict content-free observation schemas are implemented, with [coding/research instructions](docs/CHAT-INTERACTIONS.md). No actual conversation, account identifier or private browser trace is included.

The public atlas's Chat interactions section now includes a [per-operation capability matrix](specimens/chatgpt-com/v0002/chat_capability_matrix.json), [officially documented UI actions](specimens/chatgpt-com/v0002/public_chat_actions.json), and an interactive *synthetic* response-branch example. The synthetic software tools can export ordinal-only message topologies, compare structural events against candidate transitions, simulate guarded state paths, and distinguish structurally equivalent exported trees without matching original IDs. A local-only browser test suite exercises fictional completion, interruption, failure and retry, without contacting ChatGPT. See [the chat research contract](docs/CHAT-INTERACTIONS.md).

A [local-only export normalizer](scripts/normalize_chat_export.py) is also
available for export-compatible tree records. It constructs temporary
ordinal message graphs and refuses broken ancestry. Unlike the public
specimen results, it never includes raw text, original IDs or export files.

The [source-anchored client implementation trace](specimens/chatgpt-com/v0002/chat_static_impl_trace.json) records **15 narrow AST pattern matches**, **7 manually examined client operations**, **6 direct caller-to-dispatcher edges**, and module export relationships without publishing JavaScript source or private values. The current source research queue has **33 tasks: 10 in progress, 23 queued, none claimed complete**. The [Specimen Atlas](https://sguzman.github.io/viewsource/) presents these static findings and the automatic queue before optional runtime studies.

## Automatic implementation tracing

Every processed capture containing JavaScript automatically schedules a source-level investigation into functions, call graphs, client data shapes, handlers, state, network parsing, streaming, failures, persistence and render ownership, regardless of archive size. Curated feature signals optionally add dedicated chat/search/authentication/commerce/media/map/editor research chains. These are **candidate investigation tasks**, not verified features, and require code-level evidence before completion. This policy is defined in [static_profiles.json](queues/static_profiles.json), alongside the separate large-dump deep research queue. Runtime observation is not a prerequisite for exhausting captured static assets.

## Optional parsed-JavaScript evidence probe

For source-backed implementation research, the `scripts/trace_static_archive.py` tool reads a private ZIP entirely offline, safely extracts only JavaScript into a temporary system directory, parses its AST with Acorn, and prints a **content-free structural report**. Install the small developer dependency using `npm install`, then run `python3 scripts/trace_static_archive.py --input /path/to/capture.zip`. This is a research aid, not a replacement for manual function/call-chain investigation. It does not run captured JavaScript or publish filenames, source, messages, property values or identifiers. CI verifies the parser with invented source only.

## Selected-message UI evidence and automated selector scans

A new [selector-consumer study](specimens/chatgpt-com/v0002/chat_selector_consumers.json) distinguishes full selected-message ancestry, the current user-turn message window, user-message identity ancestry, automation references, and page references. The last two are feature-reference lists, **not the visible chat transcript**. Captured client code contains a React control that subscribes to the current-turn messages and binds inline and Escape-dialog buttons to guarded answer-now or skip-reasoning actions. These are static implementation findings, not observed button execution or server outcomes. The main transcript renderer has since been traced through turn preparation, typed item rendering and virtualized rows. Dynamic subcomponents and live browser outcomes remain unresolved.

The privacy-safe `--selector-trace` mode of `scripts/trace_static_archive.py` can automatically classify candidate ancestry walks, identity projections, feature-reference extractors and recent-turn controls in a newly supplied offline ZIP. As with other AST scans, candidate matches are questions to investigate, **not** accepted evidence on their own. The live source research queue remains at **10 in progress, 23 queued, 0 complete**; task evidence and completion are tracked separately.

The [response-version selection study](specimens/chatgpt-com/v0002/chat_branch_switch_trace.json) now includes the source algorithm for deriving eligible variants from a prompt's graph children, computing the selected variant index, and changing the selected node optimistically with failure rollback. Raw child count and selectable version count can differ. The **saved client implementation** is studied, not live browser execution or guaranteed backend persistence. Canonical findings E2-081 and E2-082 preserve those distinctions.

Canonical evidence E2-083 adds a source-level link between selected-node/mapping changes and the conversation page's memoized transcript derivation. The page explicitly passes those two state fields as render inputs and checks them as memoization dependencies; actual React behavior and server persistence are not inferred from source alone.

## Source-verified virtual turns and scroll placement

The captured ChatGPT client **virtualizes conversation turns**. It builds a
measured/estimated row layout, calculates a visible window using binary
search with surrounding overscan, retains selected offscreen rows, and
uses geometry changes and scroll-anchor compensation to protect viewport
position. A separate response-spacer controller can place the most recent
user turn during eligible voice scenarios. These are actual saved-client
algorithms, not observed browser motion or server behavior. The
[viewport study](specimens/chatgpt-com/v0002/chat_viewport_virtualization_trace.json)
links eleven reviewed rules to module ordinals in R-JS-066 and R-JS-072.

The selected-branch-to-virtual-window connection is recorded as E2-085, and the composer/response-spacer lifecycle as E2-086. Both are source-backed client relationships; neither asserts an observed browser scroll or server result.

The offline archive research CLI also supports `--viewport-trace`. It
extracts **candidate** virtual-list, overscan, resize, scroll-anchor,
response-spacer and input-cancellation code shapes from a private ZIP
without executing source or publishing filenames. Intake already queues
render-binding research automatically for every qualifying saved site;
this new mode supplies a reusable source-first tool to investigate it.

The [selection and code-copy study](specimens/chatgpt-com/v0002/chat_selection_copy_trace.json) adds source-level evidence E2-087 and E2-088 for scoped Markdown selection, excluded editable regions, and copy-last-code fallback/cancellation. These are guarded client implementation paths, not observed clipboard writes or live user interactions.
