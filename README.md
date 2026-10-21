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
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
~~~

The intake input path must point **outside** the repository. It is read only. For an HTML file, the same \`--input\` flag is used. Private inventory output is placed under ignored \`.work/\`; only controlled templates and task metadata are written to tracked paths. Review all generated public changes before pushing; automatic generation is not a publication-rights determination. \`process\` does not execute site scripts or request any network resources.

## Repository map

| Path | Role |
| --- | --- |
| [CONSTITUTION.md](CONSTITUTION.md), [AGENTS.md](AGENTS.md) | Mandatory publishing and research rules |
| [ontology/](ontology/README.md) | Project-level ontology: terms, relationships, semantics, evidence classes |
| [schemas/](schemas/) | JSON schemas for version records and tasks |
| [specimens/](specimens/README.md) | Approved research dossiers and immutable numbered versions |
| [queues/](queues/README.md) | Task profiles and open research items |
| [gallery/](gallery/README.md) | Human-readable gallery and machine-readable index (currently empty) |
| [docs/](docs/RESEARCH.md) | Research, evidence, limitations, and versioning procedures |
| [scripts/](scripts/) | Offline intake and validation |
| [tarium.json](tarium.json) | Independent public-project resource manifest |

## What analysis covers

Structure, routes and navigation; scripts and module loading; script responsibilities; CSS and design tokens; assets, fonts and media; accessibility and semantics; forms and interaction; client state and persistence; third-party services; requests and APIs suggested by static references; build signatures; performance hypotheses; privacy and security indicators; metadata and search discoverability; responsive behavior; dependency relationships; and differences between snapshots.

These are research **queues**, not automatic guarantees of complete observation. An accurate unresolved item is preferable to an invented explanation.

## Current contents

No website specimens have been supplied or analyzed. The gallery is intentionally empty.

## License

Project-owned code and documentation are available under [MIT](LICENSE). This license does **not** grant rights to any third-party website material submitted for private analysis.
