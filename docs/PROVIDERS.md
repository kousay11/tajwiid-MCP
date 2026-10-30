# External MCP provider design and capability audit

Audit date: **2026-10-30**. The candidate matrix and per-provider notes below are
the original *static* review (public documentation and selected source files); they
made no MCP handshake. The later **runtime audit** and the implemented gateway are
described in the next section and in [PHASE3_REPORT](PHASE3_REPORT.md). All providers
remain disabled unless an administrator opts in. Repository contents and advertised
endpoints can change.

## Runtime audit and implemented gateway (Phase 3, 2026-10-30)

Raw discovery records (tool names, annotations, original schemas) and call digests are in
`docs/provider-evidence/2026-10-30.json` (Codex) and, for the Phase 3 close-out run,
`docs/provider-evidence/2026-10-30-live-gateway.json`. Neither stores provider excerpts.

| | `quran_mcp` | `tafsir_mcp` | `quran_search_mcp` |
| --- | --- | --- | --- |
| Endpoint | `https://mcp.quran.ai` | `https://mcp.tafsir.net/mcp` | `https://mcp.quran.us.kg/` |
| Live tools discovered | 36 (14 not read-only) | 17 (all read-only) | 8 |
| Admitted by catalog | `fetch_grounding_rules`, `fetch_quran`, `search_tafsir` | `list_tafsir_sources`, `fetch_ayah`, `search_in_tafsir` | none |
| Qaloun / Abu Nashit text | none found | none found | not established |
| Scoped search for Qaloun 6:1-8 (Hafs 6:1-7) | passes boundary check | **refused** (`INCOMPATIBLE_RIWAYA`) | n/a |

Findings that matter:

- The Quran MCP README advertises Qaloon; the repository contains no Qaloon edition, the
  deployed edition used for boundary checks is `ar-uthmani-hafs`, and Wirdi AI's own
  earlier edition snapshot lists none. Treat it as unverified.
- Tafsir MCP's text differs orthographically from the local Hafs source in six of seven
  ayat of 6:1-7 (only 6:2 is equal under the pinned mapper's skeleton). The guard
  correctly refuses; unscoped search still works.
- Quran MCP marks all its tafsir editions `provisional-internal`; Tafsir MCP's
  `get_qeraat_variants` returns raw `@reader/reading@` strings. Neither gives a
  transmission path for Wirdi's corpus.
- Provider tool catalogs differ from their README tool counts (36 vs fewer; 17 vs 13), so
  admission uses the live schema hash, not documentation.

### Design versus implementation

| Design (below) | Implemented |
| --- | --- |
| `ProviderAdapter.discover()/search()` | `source_texts()` (boundary text) and `search()`; discovery belongs to the gateway |
| 3 s connect, 8 s call, 12 s total, 1 MiB | 8 s call, 16 s per operation, 35 s total (configurable, bounded), 2 MiB |
| Retry once, honor `Retry-After` | Retry once for transient/rate-limit errors; `Retry-After` is not read |
| Circuit breaker, cache | **Not implemented** (deferred) |
| `ScholarlyHit` | `ExternalHit` |
| Per-provider module files | Two adapter classes in `providers/adapters.py` |

### Licensing and terms (open questions; no data is copied or cached by Wirdi MCP)

- Quran MCP code: QFGPL-1.0 (non-commercial, network copyleft, software only; served
  Quran text, translations and tafsir are separate, per-author rights). Calling the hosted
  service as a client is not distributing or modifying that software, but self-hosting a
  fork would trigger the non-commercial and source-sharing terms. No terms of service for
  the hosted endpoint were found in the repository.
- Tafsir MCP code: MIT. `LICENSE-DATA` states CC BY 4.0 (commercial use allowed, attribution
  to Tafsir Center required) while `DATA_SOURCES.md` says commercial redistribution of
  tafsir texts needs permission from rights holders. The two statements conflict, and
  rights in the underlying works are not resolved here.
- Wirdi AI stores Tadabbur results; retention of provider excerpts there needs its own review.
- **Owner decision needed before any public or commercial release.**

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

*(This section is the original design. The implemented differences are tabulated in
"Design versus implementation" above.)*

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
