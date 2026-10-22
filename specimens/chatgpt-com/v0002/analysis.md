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
