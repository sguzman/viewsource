# Viewsource Agent Instructions

Read [CONSTITUTION.md](CONSTITUTION.md), [docs/RESEARCH.md](docs/RESEARCH.md), and [ontology/README.md](ontology/README.md) before any research or modification. Treat the public-information boundary as mandatory.

## Repository and governance

- Work in \`sguzman/viewsource\`; the default working branch is the existing \`main\` unless the owner specifies otherwise. Do not create branches or modify other repositories on your own initiative.
- This project is independent. Do not edit Tarium's central registry without a separate explicit owner instruction naming \`sguzman/viewsource\` and the membership operation.
- Never depend on, refer to, or expose private Taria data or projects. Other projects are optional only when explicitly public and their Tarium membership is verified.
- No raw captures, ZIP files, third-party source bundles, copied page content, screenshots, browser profiles, network dumps, session data, caches, or derived site assets in Git.

## Public-output protection

- Public prose, comments, tasks, issue bodies, changelogs, commits, and CI output must use factual, technical, neutral wording. Never reproduce private conversations or their distinctive language/tone, even as paraphrases.
- Never publish any token, cookie, credential, private route, personal metadata, hidden context, nonpublic source, uncertain third-party content, or private local path. Review semantics and rights, not just string patterns.
- Treat \`.work/\` and all user-supplied files as non-public. Do not quote their contents into public issues or logs. No publication of local inventories by default.
- Do not automatically place captured site resource names, sensitive URL components, CSS, JS, inline HTML, or complete asset lists in public records. Extract clearable findings and author original descriptions instead.

## Specimen processing contract

1. Use the user-supplied local ZIP or HTML file. A flat page suffices; never demand live access.
2. Create/locate the specimen in \`specimens/index.json\` with a stable slug. Do not guess site ownership or functionality.
3. Run the offline processor; inspect the private local inventory. Its ZIP reader must not unpack to disk, execute scripts, or access the network.
4. Processed capture versions are monotonic (\`v0001\`, \`v0002\`, ...); preserve earlier records. Keep raw capture hash/checksums in the ignored workspace unless separately cleared.
5. Spawn defined tasks into topical queues. Tasks are separate from findings; initial status is \`queued\`, and a task does not imply the existence of a capability.
6. Analyze HTML structure, script references, script roles, CSS, assets, navigation, forms, third-party links, behavior suggestions, network calls suggested by code, accessibility, security signals, metadata, performance, and version differences, only as evidence permits.
7. Populate record components and relationships with concise abstractions. Each finding requires evidence classification and references or must remain unknown. Mark tasks \`blocked\`, \`not_observable\`, or \`done\` accurately.
8. Publish only cleared original writing and structured summaries. Do not claim a tested live behavior on static evidence alone.
9. Refresh with new version records; identify differences and preserve previous work. Gallery examples require separate publication and licensing review.

## Quality gates

Run \`python3 scripts/validate.py\` and \`python3 -m unittest discover -s tests -v\`. Check the entire diff and intended commit message for private information and third-party material before every public write. CI checks are safeguards, not a finding that publication is authorized.

If a disclosure is suspected, stop publication and remediate without repeating the exposed content in public logs or issues.
