# Specimen Atlas

This is the public, browser-accessible research interface for Viewsource. It is an **original explanation of captured evidence**, not a replica of any specimen website.

## Contents

The generated atlas joins reviewed and in-progress specimen records to an editorial research narrative:
- Chapter navigation for HTML, CSS, JavaScript, components, logic, flow, state, assets, evidence and research tasks
- Selected, clickable ontology component graph and relationship inspector
- Interactive evidence references with confidence labels and scope
- Research tasks with dependency status, source evidence requirements and open questions
- Per-specimen/version selection, search and responsive layouts
- Day/night appearance dropdown with **System** as the default; it follows the operating-system preference unless the visitor selects Light or Dark

The site reads a generated **allowlisted** catalogue, never a capture. No copied JS/CSS bundles, saved source DOMs, archives, private application state, URLs from manifests, personal chats, or third-party fonts/images are published.

## Build

From the repo root:

~~~
python3 scripts/validate.py
python3 scripts/build_site.py --out _site
python3 -m unittest discover -s tests -v
~~~

Serve \`_site/\` using any local HTTP static server. Do not open \`index.html\` via \`file://\`, because the app fetches its JSON catalogue. The same build runs under [the Pages workflow](../.github/workflows/pages.yml) on \`main\`.

## Authoring

Narrative chapters reside in \`site/story.json\`; this is project-authored editorial content with evidence references that must exist in the published record. Components, findings and task states are generated from the versioned repository records. Never inject unreviewed raw strings, captured paths or other private evidence into site data.

New specimens appear in the selector after their public records are added. A version without custom chapters receives generic Overview, Evidence and Research Queue views rather than a fabricated narrative. Add a curated narrative only when analysis supports it.

## Deployment

The workflow uses the GitHub Pages Actions deployment source. If GitHub Pages has not been enabled for this repository, the workflow may require selecting **GitHub Actions** as the Pages source in repository Settings → Pages. The repo alone cannot guarantee Pages is enabled.
