# Viewsource ontology

The project owns a complete independent ontology for evidence-based analysis of websites. [ontology.json](ontology.json) defines the machine-readable vocabulary; [record schema](../schemas/record.schema.json) constrains each specimen version and [task schema](../schemas/task.schema.json) constrains research work items.

## Identity and versioning

- \`specimen.id\`: stable slug of a studied website.
- \`version\`: monotonically increasing snapshot index (\`1\`, \`2\`, ...), unrelated to any official site software version.
- \`component.id\`: unique in a version; identity across versions requires an explicit comparison, never guessed by a name match.
- \`relationship\`: directed edge between component IDs with an enumerated predicate.
- \`finding\`: original, source-classified explanation with an explicit evidence reference or a stated uncertainty.
- \`task.id\`: unique analytical work item for a specimen version.

## Entity taxonomy

\`Website\` owns \`CaptureVersion\`; \`CaptureVersion\` describes zero or more \`Page\`, \`DOMRegion\`, \`Script\`, \`StyleSheet\`, \`DesignToken\`, \`Asset\`, \`Font\`, \`Route\`, \`Interaction\`, \`Form\`, \`ClientState\`, \`Storage\`, \`APIReference\`, \`ExternalService\`, \`Dependency\`, \`AccessibilityFeature\`, \`Metadata\`, \`PerformanceSignal\`, and \`SecuritySignal\`.

Relationships are typed: \`contains\`, \`references\`, \`loads\`, \`styles\`, \`renders\`, \`triggers\`, \`updates\`, \`stores\`, \`requests\`, \`depends_on\`, \`navigates_to\`, \`inherits_from\`, \`associated_with\`. A reference to an API does not assert the API was invoked.

## Evidence, confidence, scope

\`observed_static\` means visible in supplied files, \`inferred_static\` is reasoning from them, \`observed_live\` requires separate verified execution, \`external_source\` requires public citation, and \`unknown\` records epistemic limits. Confidence is \`high\`, \`medium\`, \`low\`, or \`unknown\`. Source scope is \`saved_page\`, \`saved_archive\`, \`live_test\`, or \`public_reference\`.

A public \`evidence_ref\` is a sanitized abstract reference; raw filenames, full URLs with tokens, excerpts and local paths must not be copied into public records. Evidence-to-capture mapping stays outside Git.

## Evolution

The ontology itself uses \`format_version\` and \`ontology_version\`. Snapshot records bind to their current model \`ontology_version\`, while old versions remain immutable research artifacts. A breaking model change needs explicit migration; do not silently reinterpret prior findings.

## Completeness

Coverage applies to an analysis dimension **relative to the supplied evidence**. Values are \`pending\`, \`partial\`, \`analyzed\`, \`not_observable\`. A static capture can be thoroughly analyzed without being a complete model of the running website.

## Technology inventory and feature graphs (additive v1 extensions)

The ontology's **Dependency** nodes remain version-local components. A separate `technology_inventory.json`, checked by `schemas/technology-inventory.schema.json`, must link each named library to its matching `Dependency` component with `component_ref`. It records source evidence, category, likely role, and strength. **Presence of a library is not proof it powers any particular feature.**

Use a version-local `*.graph.json` matching `schemas/feature-graph.schema.json` for feature behavior. The graph has:

- **Surfaces:** UI regions explicitly linked to the specimen's component IDs and evidence references.
- **Entities:** proposed domain identities and typed fields; use opaque local keys rather than copying site identifiers.
- **Machines and states:** independent, version-scoped state machines (for example conversation selection and response progress).
- **Events and transitions:** event vocabulary, candidate guards and effects, evidence status, and a concrete plan to verify each transition.
- **Library links:** candidate dependencies on named public libraries, independently marked `feature_ownership_verified`.
- **Questions and limitations:** experiments needed before candidate edges can become observed behavior.

These are *non-breaking structured extensions* of ontology 1.0.0. Existing v0001/v0002 component records are preserved. No state graph may label a transition `observed_live` on the basis of saved HTML or JavaScript syntax; observed transitions need separate authorized, documented testing. Runtime capture must record abstract event categories and structural state deltas only, without content, IDs, token-bearing URLs, headers or payloads.
