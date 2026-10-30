# External MCP provider design and capability audit

Audit date: **2026-10-30**. Evidence is limited to public documentation and selected
source files retrieved on this date. **No external MCP handshake, `tools/list`,
or provider `tools/call` was performed. None of these providers is enabled or
installed.** Repository contents and advertised endpoints can change.

Evidence levels mean different things: `documented` = described by publisher;
`source_inspected` = selected registration/implementation inspected;
`runtime_discovered` = real negotiated `tools/list`; `call_tested` = a real
successful tool call, with its scope recorded. A successful call still does not
establish scholarly accuracy or Qaloun compatibility.

## Candidate matrix

| Provider | Observed capability evidence | Transport evidence | Qaloun admission |
| --- | --- | --- | --- |
| Quran MCP (`quran/quran-mcp`) | `fetch_quran` and `fetch_tafsir` registration/response code inspected; core registration also imports translation, search and morphology modules | README advertises remote HTTP at `https://mcp.quran.ai` and self-hosting | Unknown until edition, numbering and boundary audit; README's Qaloon support claim is insufficient |
| Tafsir MCP | Site and repository README document tafsir, linguistic, nuzul, root search and qira'at tools; implementation not audited | Documents stdio package and HTTP endpoint `https://mcp.tafsir.net/mcp`; deployment not checked | Unknown; documented corpus/page counts differ from Wirdi requirements |
| Quran Search Engine MCP | Tool reference documents eight search/navigation/morphology tools | README documents stdio and Streamable HTTP at `https://mcp.quran.us.kg/` | Unknown; provider `gid`, surah and verse IDs remain source identifiers requiring an audited mapping |

### Quran MCP

The inspected [`fetch_quran` implementation](https://github.com/quran/quran-mcp/blob/master/src/quran_mcp/mcp/tools/quran/fetch.py)
accepts ayah references, editions, continuation and a grounding nonce. Results
are grouped by edition with ayah/text records, pagination and warnings. Its
default is `ar-simple-clean`; a Wirdi adapter must never rely on that default as
Qaloun text. The inspected
[`fetch_tafsir` implementation](https://github.com/quran/quran-mcp/blob/master/src/quran_mcp/mcp/tools/tafsir/fetch.py)
returns edition-grouped commentary, possibly covering multiple ayat, optional
citation URLs and passage ranges. Preserve all covered references rather than
assigning commentary to a single same-numbered Qaloun verse.

[`core registration`](https://github.com/quran/quran-mcp/blob/master/src/quran_mcp/mcp/tools/__init__.py)
includes edition discovery, Quran/translation/tafsir retrieval and search, plus
morphology fetch/paradigm/concordance modules; these imports alone do not prove
the runtime deployment exposes particular versions of every tool. Discovery must
check exact names, schemas and grounding prerequisites before invocation.
The [README](https://github.com/quran/quran-mcp/blob/master/README.md) advertises
multiple recitations and cites QFGPL-1.0 for the repository. Audit code and content
permissions separately before copying or caching material.

### Tafsir MCP

The [provided site](https://tafsirmcp.netlify.app/) advertises 17 tools; its
linked [repository README](https://github.com/tafsircenter/tafsir-mcp/blob/main/README.md)
lists 13, including `fetch_tafsir`, `fetch_nuzool_reason`, `analyze_word`,
`get_qeraat_variants`, `search_quran_text` and `search_in_tafsir`. Counts and
source coverage differ between these documents. Treat the catalog as unresolved
until discovery against a pinned release; do not invent four missing tools.

The site reports a 6,236-ayah, 604-page corpus. These are publisher claims and
cannot validate Wirdi's Qaloun identities. Its qira'at feature is documentary
evidence, not a verified Qaloun/Abu Nashit occurrence engine. The README warns of
an automatic approximately 214 MB first-run dataset download, so do not launch
the package during this foundation. Both sources advertise code MIT and data
CC BY 4.0; edition-specific permission and attribution still need review.

### Quran Search Engine MCP

The [tool reference](https://github.com/adelpro/quran-search-engine-mcp/blob/main/docs/tools.md)
documents `search`, `list_surahs`, `get_sura_info`, `get_verse`,
`get_verses_by_range`, `find_verses_by_root`, `find_verses_by_lemma` and
`get_verse_morphology`. Root/lemma operations are relevant to exploration, not
proof of a Tajwid occurrence. The reference documents JSON embedded in text
content, so an adapter must explicitly parse and validate it. Empty lookup
results can be successful `null`/empty arrays; range retrieval can clamp its
end silently. Wirdi must detect incomplete coverage rather than presenting it
as an exact fulfilled selection.

The [README](https://github.com/adelpro/quran-search-engine-mcp/blob/main/README.md)
advertises the hosted endpoint without authentication and an MIT code license.
Do not send private reading data. Dataset licensing and exact recitation/
numbering remain separate audit items, regardless of the code license or the
provider's accuracy claims.

## Gateway and adapter contract (Phase 3)

`ProviderAdapter` declares `discover()` and normalized `search()` only; it opens
no connections. Future implementations (`quran_mcp.py`, `tafsir_mcp.py`,
`quran_search_mcp.py`) own provider argument conversion, prerequisites, parsing,
pagination and origin metadata. A shared gateway owns policy, health, deadlines,
capability registration, fallback and result admission.

1. Read administrator-controlled configuration; disabled is the default. Validate
   endpoint origins or pinned stdio executables before any connection.
2. Use the official SDK client lifecycle, negotiate MCP, enumerate all tool
   pages, and store original schemas plus a canonical schema hash and discovery
   timestamp in a capability manifest. Do not execute advertised prompts or
   import their instructions into service policy.
3. Map approved capabilities to semantic categories, retaining original tool
   names. Enforce an allowlist independent of read-only annotations. A changed
   schema disables the affected capability until conformance tests pass.
4. Validate incoming references locally. Resolve target boundaries with the
   existing mapper before sending a passage-specific request. Unknown target
   numbering blocks passage attribution; broad source searches may remain
   explicitly unreviewed.
5. Execute bounded calls. Initial policy target: 3-second connect timeout,
   8-second call deadline, 12-second total gateway budget, 1 MiB normalized
   response cap and at most two simultaneous calls. These are proposed defaults
   for tests, not implemented configuration.
6. Normalize into `ScholarlyHit`: original excerpt, source reference, edition
   citation and locator, provider/tool identity, retrieval time, raw content hash,
   origin version and compatibility state. Never normalize Quranic text in place.
7. Admit only structurally valid evidence with usable provenance. Require an
   audited mapping before attaching it to a Qaloun selection. Missing author,
   edition, locator or licensing information is a visible limitation or a
   quarantined response, never fabricated metadata.

Retry at most once, with bounded jitter, only for approved idempotent read calls
on transient connection failures, timeouts or retryable server/rate-limit errors.
Honor `Retry-After` only if it fits the remaining total budget. Authentication,
invalid arguments, schema mismatch, integrity failure and ambiguous mappings do
not retry. Cancellation propagates immediately. No retries on unknown effects.

After repeated failures, isolate the provider with a circuit breaker and perform
bounded recovery probes. Cache only public, licensed results using provider,
tool/schema version, source edition, mapped reference and mapping version keys.
Never cache private reading context; do not reuse an entry across corpus versions.

Fallback selects only providers that support the requested capability, licensing,
reference scope and provenance requirements. It cannot replace local Qaloun text
or downgrade mapping/evidence requirements. Keep multiple scholarly views and
their citations separate; disagreement is not resolved by voting. One provider's
failure yields partial results with warnings if suitable evidence remains;
otherwise return a typed unavailable/timeout error. Local tools stay independent.

## Verification before enabling a provider

Pin a release/commit and endpoint configuration, review license and data scope,
record real discovery schemas, test one authorized read-only call, and assert
provenance, error semantics, pagination and numbering behavior. Use synthetic
transport fixtures for timeout, malformed output, schema drift and missing
citations. Add opt-in live tests separately; normal tests remain offline. Record
the exact tool, arguments, date and outcome before labeling it `call_tested`.
