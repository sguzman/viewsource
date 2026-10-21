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
