# Offline structural census

After a saved HTML or ZIP capture has been processed into a specimen version, use:

~~~sh
python3 scripts/static_census.py --slug example --version 1 --input /path/outside/repo/page.html
~~~

This uses **only** local capture files, performs no network calls and executes no page scripts. HTML content is tokenized by the Python standard-library parser. Source text, script code, embedded application JSON, attribute values, resource paths, conversation data, page titles, and identifiers are never serialized into the result. The output is an **ignored private** \`.work/<specimen>/vNNNN/static-census.json\` file.

This census counts semantic HTML elements, selected accessibility/state attributes, external resource-reference categories, script/data element types, static implementation signatures, CSS media-query types, and file-input attributes. ZIPs are read without extraction and with archive path, size, symlink, and member checks. Limits apply to individual HTML sizes and total pages; omitted pages are counted.

It is intentionally unable to answer whether a button works, whether server endpoints exist, whether inaccessible assets contain additional rules, or whether the captured state represents the site generally. Its recognized signatures (for example React Router streaming helpers) are observations of syntax, not proof of execution.

The private census is evidence for subsequent manual or agent-supported **original technical analysis**. Promotion to the public version record requires checking scope, the meaning of each counter, and publication rights. Do not move the census into the repository or attach raw captures to public issues. Never use source-string exports to bypass the public-information boundary.

Run regression tests using \`python3 -m unittest discover -s tests -v\`.
