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
