# chatgpt.com — Captured research v0002

**Status:** Researching. **Capture:** 2026-10-22 00:38 UTC (supplied snapshot naming). **Evidence:** locally inspected ZIP. **Previous version:** [v0001](../v0001/analysis.md).

Only original, privacy-reviewed findings and structured metadata are committed. No raw ZIP, HTML page, manifest URLs, scripts, stylesheets, font or image bytes, embedded JSON state, account identifiers, session material, or copied conversation text enter Git.

## Capture completeness

The ZIP contains 238 entries: source DOM, derived offline HTML preview, resource manifest, capture notice, and 234 website assets. The manifest reports 29 unsuccessful resource attempts: 17 HTTP 403, ten HTTP 404, two timeouts. These do not prove broken live functionality. A preview is a derived artifact, not a second observed page.

| Resource category | Captured files | Bytes |
| --- | ---: | ---: |
| JavaScript | 144 | 28,066,928 |
| Stylesheets | 17 | 2,340,628 |
| Font files | 60 | 1,169,636 |
| Images | 12 | 725,265 |
| Additional HTML document | 1 | 13,236 |

All **234** resource instances are enumerated by category and capture-local ordinal in [resource_inventory.json](resource_inventory.json). Raw paths and URL query strings are excluded. These identifiers do not persist across captures without explicit matching.

## Rendered page structure

The rendered source DOM contains 130 button elements, 26 anchors, 175 inline SVG elements, two nav regions, two header and aside regions each, one main region and one form. It has 19 script elements: 16 executable inline scripts, two non-executable JSON data scripts, and one external script reference. A separate offline preview must not be counted as another live route.

There are 72 modulepreload link elements and 18 stylesheet links in the DOM. Reference counts are not unique downloaded-file counts; the archive contains 17 captured stylesheet files.

## JavaScript architecture — first source-level pass

The 144 captured bundles total approximately 28 MB and include static code indicators for network calls, state persistence, streaming, media, workers, and asynchronous module loading. In source-pattern scans:

- 30 JavaScript assets contain a fetch-call text pattern.
- 8 contain WebSocket terms; 2 contain EventSource terms.
- 26 contain storage-related terms.
- 10 include dynamic-import patterns; 3 contain WebAssembly-related terms.
- 5 contain WebRTC-related terms; 5 contain AudioContext terms.

These are **pattern hits**, not proof of module execution, public product capabilities, network transactions, or endpoint implementations. Call paths, route ownership, dependency relationships, and unexecuted features are distinct follow-up research tasks.

## CSS and responsiveness

The 17 CSS assets contain 627 media rule occurrences, 735 supports rules, 504 container rules, 26 font-face rules, 164 keyframes, 8,135 CSS custom-property declarations, 23,269 variable references, 497 focus-visible occurrences, and 168 reduced-motion references. Many declarations are repeated/generated. These are syntax counts, not distinct design-token, breakpoint or rendered-component counts.

The resource corpus now supports deeper design-token and responsive-regime research, without requiring a live browser.

## Fonts and visual assets

Captured images: eight SVG, three PNG, one WebP. Fonts: 21 WOFF2, 20 WOFF, 19 TTF files. Format variants and subsets may share actual families; no family identification was inferred solely from format and asset count. Third-party binary resources stay uncommitted.

## Accessibility and client state

The source DOM contains 152 aria-label, 160 aria-hidden, 93 aria-expanded, five aria-controls, five aria-live, and 33 tabindex attributes. These reveal markup conventions, not verified screen-reader performance or focus behavior.

JavaScript references browser-storage APIs and includes saved application state scaffolding. Serialized user/application values remain private. A captured string referencing a service is not evidence that the client contacted it.

## Performance, network and security limits

Asset counts and static CSS/JS inspection support source-level workload hypotheses only. No runtime bandwidth, latency, CPU, memory, request waterfall, live security audit or HTTP response-header policy inspection was performed. The capture manifest includes URLs and the source includes user-specific state, so publication uses ordinal descriptors and aggregates only.

## Relationship to v0001

v0001 captured standalone HTML, with 102 buttons and 131 inline SVGs in that view; v0002 captured a different DOM state with 130 buttons and 175 inline SVGs, plus bundled resources. This **does not establish a website product change**. Different page state, session and capture depth remain confounders. Cross-version asset matching needs evidence rather than assuming ordinal continuity.

## Queue state

The v0002 task graph has 18 standard research profiles plus 16 source-driven follow-up tasks, spanning scripts, styling, network, behavior, state, assets, accessibility, architecture, evolution, and quality. Initial inventories are evidence-closed; interpretive work remains queued. Progress refers only to the supplied snapshot.

## Evidence keys

- E2-001: archive and derived preview roles
- E2-002: rendered DOM census
- E2-003: capture manifest success/failure categories
- E2-004: JavaScript asset census
- E2-005: stylesheet corpus census
- E2-006: fonts, images and embedded resource types
- E2-007: source DOM versus offline preview
- E2-008–E2-011: source-pattern indicators, not live execution
- E2-012: static CSS syntax metrics
- E2-013: static accessibility markup
- E2-014: script/data distinction
- E2-015: excluded private capture data
- E2-016: v0001 comparison constraints
- E2-017: sanitized 234-resource ordinal inventory

## Deeper offline source analysis (E2-018 through E2-025)

### Candidate module-reference graph

The submitted manifest identifies 144 JavaScript resources. Comparing their captured public asset basenames as literal text within the other saved JavaScript bundles yields **300 distinct directed source-to-target reference pairs**, across ten source bundles and 71 target bundles, with **5,469 aggregate textual occurrences**. The often-repeated matches are consistent with generated asset maps; they are not a parsed JavaScript import graph and should not be interpreted as executed network fetches.

A version-local machine-readable graph appears in [source_analysis.json](source_analysis.json), represented by ordinal ranges instead of publishing captured asset filenames. The source list and target list are independently counted; source files can also be targets. Future versions must re-establish mappings rather than comparing ordinals.

### Preloaded versus bundled resources

All 72 modulepreload references observed in the DOM have corresponding saved JS resource entries. All 18 linked stylesheet references resolve to captured CSS, comprising 17 unique files. Presence and preload linkage establish resource discoverability in this snapshot, not whether the browser evaluated each module.

### Source-code primitives

More specific pattern matching across the JavaScript assets identifies **186 fetch-call patterns** in 30 files and six \`new WebSocket(...)\` syntax patterns in six. Dynamic \`import(...)\` syntax appears 23 times in ten files. Terms for EventSource were visible in the initial census, but this pass did not find a corresponding explicit constructor expression. No API request/response, endpoint behavior, or authentication property was observed.

State and coordination signatures include \`localStorage\` in 18 files, \`sessionStorage\` in 17, IndexedDB in four, \`BroadcastChannel\` in seven, and \`postMessage\` call patterns in 23. Worker constructors appear in eight files, service-worker references in one, and WebAssembly member access in one. JavaScript also contains media-device and audio-context indicators, plus IntersectionObserver, ResizeObserver and MutationObserver names. These categorize **available source code**, not enabled or user-visible features.

### CSS organization and responsive regimes

The captured CSS contains **2,509 distinct custom-property names** across 8,135 declarations. Prefix families include color tokens, application colors, text/heading font tokens, border and focus-ring colors, shell layout values, and component-specific tokens. Since repeated generated variants can redeclare a property, the number of declarations is not the number of individual design tokens.

The source includes 167 width-media queries, 209 hover-related conditions, 68 pointer-related conditions, 168 reduced-motion conditions, and 11 print conditions. Captured container queries include 269 width checks, 258 \`style(...)\` tests, and two height checks. Some queries satisfy more than one category; each count is a tagged source occurrence, not a unique rendered layout state.

### True font metadata

The 60 fonts were inspected using internal name tables, not guessed from their extensions. They represent thirteen families and 23 family/style combinations. **OpenAI Sans** has three WOFF2 variants (Regular, Medium, Semibold); the other twelve families belong to **KaTeX's mathematical typography** and mostly repeat across WOFF2, WOFF and TTF formats. No font binary, licensing assertion over its content, or copied font metadata record was committed.

### Evidence boundaries and work queue

The linked-source, static storage, responsive taxonomy, and font-identity research tasks have been closed **within the available capture scope**. Other tasks remain queued for qualified control-flow interpretation, DOM event-to-bundle linkage, media behavior, image roles, accessibility behavior, and final review. This dossier is still in **researching** status. The source_analysis file contains aggregates and ordinal links only; it is not a raw source extraction.

## Final source-limited deep analysis

The following results were obtained by **reading the provided ZIP offline**, without running scripts, replaying the page, making network requests, collecting browser telemetry or publishing untrusted site source. Cross-reference [source_analysis.json](source_analysis.json) for the candidate asset-text graph and CSS/font taxonomy, and [deep_analysis.json](deep_analysis.json) for the new aggregate inspection.

### Remote invocation syntax and streaming (E2-026)

The 144 captured JavaScript files contain 186 text-pattern matches to a fetch call in 30 bundles. At the start of their first argument, 141 are identifier-or-call expressions, 31 other expressions, and fourteen literal or template starts. This is a **lexical categorization**, not a complete callsite AST, request destination list, or live trace. Six explicit WebSocket construction patterns were found. EventSource is mentioned by the available source, but this scan found no literal \`new EventSource(...)\` constructor expression. Sixteen \`getReader()\` and 27 \`new TextDecoder()\` patterns show code associated with streaming and decoding. None establishes which requests actually ran or succeeded.

### Event and component machinery (E2-027)

The captured HTML contains 130 buttons, all explicitly \`type="button"\`, one form with four file-type inputs, and no inline \`on*\` event-handler attributes. JavaScript references \`addEventListener\` in 69 bundles (987 call patterns) and \`removeEventListener\` in 64 bundles (815 patterns). Constructors for mutation, resize and intersection observers occur 65, 90 and 52 times respectively; animation-frame scheduling appears in 40 bundles, totaling 144 patterns. This documents a substantial event/observer machinery. A compiled listener factory may be used by many components, and **which listener belongs to which DOM control cannot be proven from this capture**.

### Client state, persistence and coordination (E2-028)

Explicit browser storage patterns comprise 55 localStorage reads, 34 writes and 37 removals; 40 sessionStorage reads and 46 writes; four IndexedDB open calls and ten BroadcastChannel constructors. Twenty-three bundles also contain postMessage call patterns, and seven contain Web Crypto \`crypto.subtle\` member access. These are potential state-transport mechanisms present in captured code; no keys, values, cross-tab messages or authorization materials are included.

### Media behavior clues (E2-029)

Saved JavaScript contains one \`RTCPeerConnection\` construction pattern, three \`getUserMedia\` calls, one \`getDisplayMedia\` call, and one \`AudioContext\` construction pattern. These support a **source-code pathway classification** involving real-time media, microphone/camera requests, screen capture, and audio processing; they do not establish that the saved session used any of them. Permission outcomes, media routing and successful connections remain unknown.

### Styling, selectors and accessibility-sensitive UI (E2-030, E2-033)

The captured CSS includes 570 \`:has()\` selector occurrences, 4,081 \`:where()\` occurrences, 493 \`:focus-visible\` occurrences, 88 grid-display and 334 flex-display declarations, 504 container rules, 33 \`@layer\` occurrences, and 103 view-transition-related text matches. A large number of generated declarations and shared utilities can multiply occurrence counts. Its static focus and motion rules **do not prove accessible interaction**.

In the DOM, accessible-state markup includes 61 \`aria-haspopup\`, 13 \`aria-busy\`, five \`aria-live\`, a dialog role and a textbox role, beyond the previously counted labels, expanded attributes and tabindex markers. Focus movement, status announcements and assistive-technology behavior require execution and were not tested.

### Visual resources and supplemental document (E2-031, E2-032)

The asset set includes a large SVG sprite (ordinal \`R-IMG-004\`) with **911 reusable symbol definitions** and 1,349 path elements, alongside smaller SVGs. Three PNG dimensions are 48×48, 180×180 and 120×120; a WebP is 512×512. The icon-sprite structure and icon-size raster dimensions are grounded observations; a screenshot-to-asset placement map is not. All binary graphics and vector source remain outside Git.

The separate embedded HTML resource is a lightweight document containing three script tags and one linked script reference, not an independently visited route. Its runtime relationship to the main page was not demonstrated.

### Security and capture boundaries (E2-034)

The saved DOM has nonce attributes on 18 script and 74 link elements, a sandboxed iframe, and an iframe referrer-policy attribute. JavaScript also contains Web Crypto API syntax. Nonces in a saved HTML file do not prove effective CSP header enforcement. No HTTP response-header, authentication, transport, cryptographic implementation, or exploit validation occurred, and none should be inferred.

### Comparison to v0001 (E2-035)

The original HTML capture had 102 buttons, 131 SVG elements and fifteen anchors. v0002 has 130 buttons, 175 SVGs and 26 anchors. The new ZIP contains an extensive bundle corpus absent from the initial standalone HTML. These are **differences in observations and capture completeness**, not verified changes in ChatGPT releases. No stable asset identity or matched route/session state was established between the captures.

### Completion and explicitly unobservable tasks (E2-036)

All 34 v0002 research tasks now have terminal dispositions: 32 complete within available **static** evidence, two not observable. The unobservable items are dynamic accessibility behavior and reliable mapping of saved DOM controls to runtime event-handler ownership. They are not replaced with invented execution traces. Remaining unknowns about live network calls, remote services, server internals, feature flags, or device permissions are documented as intrinsic capture limitations.

**Reviewed** means the supplied ZIP has been exhausted for this evidence-bounded research pass. It does not mean the complete ChatGPT website, runtime, or private infrastructure has been reconstructed.

## Active deep research — first source-verified batch

The first static review ended with known unresolved implementation questions; the specimen was then reopened with a persistent 57-task dependency graph. This batch completed thirteen deep tasks using stronger evidence than the earlier lexical counts. The companion [ordinal-only source report](phase3_analysis.json) intentionally omits original asset names, captured URLs, page text, accounts and copied source.

**Document hierarchy and routing (E2-037 through E2-039).** The supplied ZIP contains 238 archive entries, including 234 captured resources, with 29 separate unsuccessful resource attempts. Both navigation regions in the saved DOM sit within asides; the form sits within main. Closest-landmark grouping places 70 buttons in navigation and 42 directly within main, with the remaining buttons under headers, asides, the form or no listed landmark. Twenty-six anchors comprise eleven site-relative, fourteen external-absolute and one fragment-only target. This does not identify their click handlers or disclose the actual destinations.

**Entry and module syntax (E2-040 through E2-042).** Fourteen classic inline, two module inline and two JSON script elements accompany one external script element. The 72 modulepreload links all resolve to saved JS resource ordinals; the external script resolves to another ordinal. Parsing all 144 saved scripts into JavaScript syntax trees produced zero parser diagnostics. The resulting graph identifies **236 literal static imports** that resolve to 236 ordinal pairs involving eight importing files and 71 targets, including eight self-ordinal pairs requiring interpretation. The scanner also found eighteen dynamic import expressions. This parsed graph is not the same thing as the earlier 300 filename-text candidate pairs; neither establishes which modules actually executed. One source-map reference marker exists, but the ZIP includes no source-map resource and no verified original source tree.

**CSS and icon mapping (E2-043, E2-044).** Eighteen stylesheet link elements resolve to seventeen unique captured CSS assets; one target is repeated. The CSS includes 33 layer text occurrences, 627 media at-rules and 504 container at-rules, but the browser's winning cascade has not been measured. All 92 SVG use nodes resolve to the captured sprite asset and match 23 different symbol identifiers out of 911 definitions. The original graphic, IDs and element markup remain excluded from publication.

**Accessible structure, policy boundaries and capture failures (E2-045 through E2-047).** The rendered DOM includes nested landmarks, 152 aria-label, 93 aria-expanded, 61 aria-haspopup, and seven status-role indicators. Neither focus movement nor assistive-technology behavior was instrumented. Nonce attributes and an iframe sandbox are visible, but response CSP headers are not. The 29 resource failures include seventeen HTTP 403, ten HTTP 404 and two other failures; these are capture outcomes, not confirmed product defects.

Thirteen deep tasks now have evidence-backed completion states. The other 44 deep tasks remain queued, including detailed state ownership, network contracts, CSS-to-component ownership, behavior pathways and end-to-end runtime reconstruction. No unobserved behavior is treated as confirmed.

### CSS semantic families, responsive conditions and motion (E2-048 to E2-050)

A second CSS-specific pass inventoried the **relationships** among custom-property definitions and uses, rather than exposing the names themselves. Across the 17 saved stylesheets, there are 2,509 distinct defined property names, 8,135 definition occurrences, and 23,269 variable references. Heuristic prefix groups distinguish color (1,032 distinct definitions), typography (325), spacing (69), border/shape (32), depth/effects (53), dimensions (28), motion (14), and an unspecific remainder (956). Some groups appear more often as references than declarations. Exactly 607 distinct referenced property names lack a matching definition in this captured CSS corpus; runtime injection, inheritance, absent assets and other sources remain possible.

For responsive behavior, 573 bounded media-rule preludes and 454 bounded container-rule preludes were classifiable, from lexical totals of 627 and 504. Among overlapping media categories were 159 width, 178 hover, 60 pointer, 168 reduced-motion, and eleven print matches. Container categories included 258 style-query, 196 width-query and two height-query matches (conditions can overlap). Pixel-width threshold counts are intentionally published only in broad bands; these are not a definitive breakpoint or visual-state map.

The corpus also shows 164 keyframe at-rules, 438 transition declarations, 287 animation declarations, 270 duration declarations, 493 focus-visible selector matches, and 168 reduced-motion query preludes across ten stylesheets. The [CSS analysis report](phase4_css_analysis.json) details these bounded methods. It is not a claim that any animation ran or any accessibility setting was tested. Three additional CSS deep-research tasks are complete; computed cascade and component-to-token ownership remain open.

## Completed offline deep research and evidence boundaries (E2-051–E2-063)

This final source-bounded review builds on the previously published DOM, JavaScript import, CSS and graphic findings. An additional offline syntax-tree and structured stylesheet pass produced the [sanitized source-system report](phase5_system_analysis.json). **No original HTML, JavaScript, CSS, file names, URLs, login material, account identifiers, messages or captured images are published.**

### Modules and loading (E2-051, E2-052)

All 144 captured JavaScript resources were parsed, yielding roughly 9.27 million syntax nodes and 120,699 function-like nodes. Fixed browser API signatures occur in overlapping groups: 48 bundles with React-like callsites, 54 with network-related callsites, 89 with events/observers and 46 with storage/message-state patterns. These overlap and **do not prove that any particular module owns a product feature**. The document has 72 matched modulepreloads; the code includes 236 parsed static imports and eighteen dynamic import expressions. None is an executed module-load trace.

### Logic, persistence and transport (E2-053–E2-055)

The static code includes 997 listener registrations, 822 removals, 144 animation-frame calls and multiple observer constructor types. Fixed-name state signatures include 118 getItem, 102 setItem and 78 removeItem method calls; the capture also contains eight Worker constructors, eleven BroadcastChannel and 25 MessageChannel constructors, plus 77 postMessage calls. These generic method names do not identify actual storage ownership or any message values.

AST-level network syntax includes 178 fetch calls, 244 AbortController constructors, sixteen getReader calls, 33 TextDecoder constructors, six WebSocket and three peer-connection constructors. Five nearest lexical function scopes contain both fetch and streaming signatures, and six combine fetch and abort signatures. Lexical co-occurrence is **not proven runtime dataflow, a real API contract, authorization, retry behavior or successful media/streaming communication**.

### Styling, typography, accessibility and budget (E2-056–E2-059)

Of 2,183 saved DOM elements, 1,688 have CSS class attributes. There are 744 distinct DOM class names; a limited unescaped-class parser found 3,776 distinct class names in 16,983 CSS rules, with 359 shared names and 1,666 DOM elements containing a shared label. It is a vocabulary-overlap map, **not a computed CSS cascade**, component ownership or proof of responsive rendering.

Font metadata separates 57 mathematical typesetting and three interface-sans assets among sixty captured font files. Accessibility indicators include ARIA annotations, focus-visible selectors and reduced-motion source conditions, without tested keyboard, focus, announcements or compliance.

The archive holds 28,066,928 JavaScript bytes, 2,341,104 CSS bytes, 1,169,636 font bytes and 725,265 image bytes. The five largest scripts account for 36.38 percent of captured JS size, the ten largest 57.71 percent. These saved byte figures are **not live transfer sizes or a measured performance waterfall**.

### Source boundaries and research dispositions (E2-060–E2-063)

The site's navigable research story connects observed DOM/landmark structures, declared asset references, parsed static imports, CSS class overlap and generic browser API constructs. It is a conditional *research model*, not a claim of observed chronological behavior.

Precise React/component props and ownership, control-to-handler mapping, network contracts, authentication enforcement, actual uploads, state transitions, media operations, assistive-technology interaction and like-for-like release changes are **not observable from this static ZIP**. They are recorded explicitly as unknown or unobservable, not counted as completed product reverse engineering.

**Final v0002 task audit:** 37 deep tasks supported within static scope, twenty deep tasks not observable. Together with the first pass, the version has **69 completed, 22 explicitly unobservable, and zero queued** tasks. The record is reviewed **for the supplied offline evidence only**. Further investigation of the live product would require new, separately scoped and authorized evidence.
