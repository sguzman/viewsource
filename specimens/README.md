# Specimens

\`index.json\` is the canonical specimen list. It is intentionally empty until the first site is queued.

A queued specimen has a stable slug and sanitized origin, but no version. Processing the first supplied snapshot creates \`<slug>/v0001/record.json\` and \`analysis.md\`, followed by further numbered directories on later captures. Each version is a snapshot **within this research project**, not the website's own release version.

All public files contain original research metadata and reviewed analysis only. Source ZIPs, copied pages, saved scripts, styles, network traces and asset inventories are not stored here. Private inventories belong under ignored \`.work/\`. See [research protocol](../docs/RESEARCH.md).
