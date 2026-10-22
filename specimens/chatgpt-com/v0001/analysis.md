# chatgpt.com — Internal specimen v0001

**Status:** Research in progress. **Capture class:** one standalone saved HTML page. **Scope:** a single authenticated conversation view, not a site-wide survey. **Internal version:** 1 (not an official product version).

## Evidence and publication boundary

This dossier contains only original, sanitized technical observations and aggregates. The supplied source document is not committed, and none of its session identifiers, conversation content, embedded state values, captured URLs, raw JavaScript, stylesheet source, screenshots, or account identifiers are published. Evidence labels below identify inspected source categories rather than exposing the source itself. A private source-to-label inventory can be reconstructed when the original capture remains available.

## Scope and structure

- A standard saved HTML document is present, with head and body sections. It contains the visible application shell and nested interface DOM.
- Observed structural tags: 2 header, 2 navigation, 2 aside, and 1 main element; 619 div and 388 span elements. These counts describe this single snapshot only.
- The markup contains sidebar/navigation markers and a main content region. One form and four inputs are present, but their runtime submission outcomes were not verified.
- The captured layout is not evidence that all routes, logged-out states, responsive states, or account configurations share the same structure.

## Script inventory and loading

- 12 script elements occur in the saved HTML.
- 1 refers to an external JavaScript file whose contents were not included with this upload.
- 11 are inline script elements, of which **1 is non-executable application/json data** (approximately 557 KB of serialized application state) and **10 are executable inline scripts** (approximately 17.4 KB of code).
- The theme bootstrap contains browser-preference and local-cache handling. Its successful runtime operation was not independently tested.
- No conclusion about the complete application bundle, component framework internals, server-side code, or network contracts can be drawn from the absent external JavaScript resource.

## CSS, appearance, and responsiveness

- The HTML references 25 external stylesheets, none of which were uploaded.
- 14 inline style elements total approximately 52 KB of inline CSS.
- Light and dark themes are expressed through CSS custom properties. The source includes browser color-preference logic and explicit theme styling.
- Media-query styling and responsive-related attributes appear in the captured markup and inline styles. Exact behavioral breakpoints and final computed styles require the missing assets or browser observation.

## Assets, forms, and accessibility

- 131 inline SVG elements and 102 button elements are present; one img element is visible.
- ARIA markup includes 127 aria-label attributes, 113 role attributes, and 13 aria-labelledby attributes. These demonstrate annotation, not verified accessibility.
- The resource references include 25 CSS files, 1 JavaScript file, and 1 image in a companion saved-page directory not provided with the HTML.
- Media, fonts, icons, and other binary resources cannot be inspected beyond the standalone page itself.

## Client state, services, and security observations

- Inline startup logic checks theme selection and local storage. This is direct static evidence of references, not proof of persistence in every execution environment.
- The HTML embeds an application-state JSON payload containing conversation-linked data. Account-linked identifiers also appear in page attributes. Public output therefore excludes payload contents and identifier values.
- Any endpoint or client-service interpretation requires direct evidence in available code; no live request or response was captured by this study.

## Architecture and relationships

The saved page links an application shell to navigation, content, form controls, themed CSS, scripts, and page assets. The appearance bootstrap refers to browser preferences and locally cached settings before presenting the selected palette. The public machine-readable version record contains these as typed components, findings, and directed relations with evidence classes.

## Known limitations and next research

The companion saved-page folder is absent, so referenced scripts, complete CSS rules, asset files, imports, and much of the behavior remain unobservable in this upload. Study the available inline markup first, then separately inspect an optional, locally supplied resource archive if one is later provided. No live crawl is required. This is internal version v0001, so change comparison has no baseline.

## Evidence classification key

- **E-001:** Document root and head metadata (sanitized).
- **E-002:** Semantic structure and application-shell DOM census.
- **E-003:** Script element type/reference census.
- **E-004:** Inline appearance initialization code structure.
- **E-005:** Stylesheet links and inline CSS structures.
- **E-006:** Controls, SVG, form elements, and accessibility attribute census.
- **E-007:** Relative companion-resource reference counts.
- **E-008:** Sensitive state-presence classification, without values.

All listed observations are **observed_static**. Live behavior, backend implementation, and whole-site completeness remain unknown. Existing tasks in the per-version queues record further required analysis.

## Static analysis continuation

### Streaming application architecture (E-009, E-010)

Four inline scripts interact with a React Router streaming controller, either enqueueing serialized route-loader payloads or closing a stream. A separate set of streaming-boundary DOM replacement helpers is consistent with React's incremental server-rendered content machinery. This identifies **source-level mechanisms**, not a verified live sequence of requests or successful hydration. No serialized route payload content is included in the public analysis, because the payloads contain account- or conversation-linked values.

The page's script-element count must not be mistaken for the application-code size: the large JSON block is data, and several executable wrappers merely embed serialized state. The missing referenced script file prevents module-level reconstruction.

### Session-specific launch pathway (E-011)

An early bootstrap script inspects a browser location fragment and uses session storage to carry transient launch-related state. This is a source-level observation of a pathway, not a demonstration that the pathway was exercised in the captured session. Fragment values and stored contents are excluded.

### Scope-specific environment (E-012)

The document root includes desktop application attributes identifying a Codex Linux browser environment. This is a material scope qualifier: a saved ChatGPT page observed in one application window may differ from other browsers, operating systems, login states, plans, and presentation surfaces. The captured attribute names justify the classification, but identifying values are unnecessary to publish.

### Controls and interactive hooks (E-013, E-006)

The single saved DOM contains fifteen anchor elements, four file inputs, and 102 buttons. Three file-input elements advertise multiple selection, and one has a capture attribute; actual file selection or submission was not tested. Seventy \`aria-expanded\` attributes, five \`aria-controls\` attributes, and 108 \`data-state\` attributes indicate multiple declarative state and accessibility hooks. They are not evidence of successful keyboard navigation or fully correct accessibility.

### Captured CSS behavior (E-014)

Four inline \`@media\` rules are visible: two reduced-motion rules, one hover-related rule, and one width-related rule. These supplement the light/dark theme tokens and browser appearance bootstrap described above. Computed styles and rules in the twenty-five unavailable external stylesheets remain unverified.

### Queue resolution for this pass

The captured HTML's document structure, script-element inventory (including code/data distinctions), and head metadata inventory have been analyzed within **this capture's scope**. Navigation, responsiveness, component architecture, client-state evolution, assets, performance, live service behavior and security implications remain partial or pending as indicated in the machine-readable record. A successful static inventory never constitutes proof of runtime operation.

## Final first-capture research pass (source-limited)

### Navigation and page composition (E-015)

Fifteen anchors occur in this saved page: fourteen HTTP(S) absolute references and one fragment link. Three links request new-tab navigation with \`noopener\` and \`noreferrer\`. The DOM has two navigation containers, two headers, two asides, and one main landmark, with a nested conversation/application composition. These counts capture the one rendered session view; they do **not** enumerate every application route, dynamic menu, or navigation destination. Destination addresses are deliberately not copied to public research outputs.

### Design-system topology (E-017)

The fourteen inline style elements contain 497 custom-property **declarations**, not necessarily 497 distinct custom properties; repeated light/dark values are included. There are 261 \`var()\` references, fourteen CSS \`@keyframes\` declarations, three layer directives and 104 elements with inline \`style\` attributes. Four media rules are visible, with reduced-motion, hover/pointer, and width-sensitive cases. External stylesheet contents and computed cascade outcomes are not available, so styling coverage refers strictly to inline content and link structure.

### Exhaustive available external-reference inventory (E-025)

See [resource_inventory.json](resource_inventory.json) for 31 individual resource references with ordinal identifiers, kinds, and source-availability flags:

| Reference class | Count | Captured source available? |
| --- | ---: | --- |
| Linked CSS files | 25 | No |
| External JavaScript file | 1 | No |
| Referenced image file | 1 | No |
| Favicon links | 2 | No |
| Touch icon | 1 | No |
| Iframe document | 1 | No |

Each resource gets a separate typed ontology component and relationship to the page. Ordinal identifiers are version-local and intentionally exclude file paths, URL values, and other captured identifiers. Inline SVG (131 occurrences) and inline CSS/script elements are represented by separate component groups.

### Accessible markup versus tested accessibility (E-020)

The static DOM has 147 \`aria-hidden\`, 127 \`aria-label\`, seventy \`aria-expanded\`, five \`aria-controls\`, five \`aria-live\`, and 29 \`tabindex\` attributes. It also includes declarative presentation, group, button, and list roles. This documents semantic hooks and observable state annotation. The correct focus order, screen-reader experience, live announcements, and interactive toggle behavior remain **unverified**, not implicitly passing.

### Interactive markup versus executed behavior (E-013, E-006)

One form, four file inputs and 102 button tags are present. All observed button tags use \`type="button"\`, so their behavior cannot be inferred from native form submission alone. The four file inputs describe possible file-selection affordances, but the missing JS bundle and absence of an executed browser test prohibit reliable reconstruction of event-handler registrations, drag/drop flows, modal lifecycles, upload endpoints or subsequent state transitions. This research task is marked **not observable from the available capture**, rather than inventing a control flow.

### Client state and services (E-004, E-009, E-011, E-019)

The appearance bootstrap reads client-side preferences and browser media signals. Another source path uses session storage and a location fragment for transient launch data. Inline route-stream logic appends serialized application state, but the values are deliberately excluded from public output. A search of executable inline code shows **zero** occurrences of the \`fetch()\` call pattern and no references to \`XMLHttpRequest\`, \`WebSocket\` construction or \`EventSource\` construction. These negative observations concern the **small inline script subset only**. They do not imply that the application itself is offline, service-free, or request-free. Actual API contracts, remote persistence and third-party service graph remain not observable without the external JS or network evidence.

### Performance and privacy/security clues (E-021, E-022)

One external JavaScript reference and 25 linked CSS resources, alongside ten inline executable scripts and fourteen inline styles, describe the captured loading topology. The code includes early appearance initialization intended to avoid a theme flash. No loading timings, request counts, waterfall, memory data or browser performance entries were supplied, so no numeric performance judgment is justified. The saved markup exposes nonce-bearing script elements, a referrer directive, one sandboxed iframe and safer \`noopener\`/\`noreferrer\` handling on three new-tab links. These are **static indicators only**: no CSP response header, authorization mechanism, privacy policy enforcement, security vulnerability or remote trust boundary was evaluated.

### Cross-cutting architecture (E-023)

The observed client-side diagram is: a document shell containing navigation/content and a serialized route-data payload; inline streaming scripts coordinate React route-loader data and streamed boundary updates; an appearance bootstrap selects palette state; inline and referenced styles apply the interface design language; user controls and SVG elements are present in the rendered shell. Typed relationships and individually enumerated resource references live in [record.json](record.json) and [resource_inventory.json](resource_inventory.json). This is a **source-derived partial architectural model**, not a claim about the unobserved complete production backend.

### Review disposition (E-024)

All available HTML structure and inline sources have received a documented static-evidence pass. Four tasks close as **not observable**: external module reconstruction, executed interaction behavior, remote-service mapping, and comparison against an earlier capture. Every other task closes as **done within the v0001 evidence scope**, preserving the limitations above. This does not designate the complete ChatGPT website as fully analyzed. The next independently supplied dump is a separate capture version; it can fill the missing evidence, without rewriting v0001's historical observations.

The raw saved HTML, personal data, private application-state payloads, and unprovided external files are excluded from the repository. This dossier contains only original explanations and aggregate counts derived from the source.
