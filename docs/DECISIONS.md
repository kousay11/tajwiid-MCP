# Architectural decisions and trade-offs

Foundation decisions accepted 2026-10-30; Phase 2 refinements below are based
on read-only source evidence. Revise through explicit versioned decisions.

| Decision | Justification | Trade-off / revisit trigger |
| --- | --- | --- |
| Independent Python 3.12+ `src/` package using Hatchling | Standard packaging, clean installed imports and reproducible entry point | Existing app dependencies must remain behind ports |
| Official `mcp==2.3.0`, `MCPServer` v2 API | Verified current package and tested SDK surface; one SDK handles server and outbound clients | Exact pin requires reviewed security/version updates; do not mix v1 or third-party FastMCP examples |
| stdio only in executable Phase 1 | Local Ubuntu development without a public listener or premature auth service | HTTP/ASGI deployment remains a later explicit task |
| Five operational read-only tools; three unregistered Tajwid proposals | Data/mapping admission gates now pass; no fake Tajwid handlers | Unconfigured sources return typed unavailability |
| Small meaningful modules, no empty engine/adapters | Keeps transport, contracts, data ports and providers distinct without fake implementations | Add services, validators and actual adapters incrementally |
| Required corpus/version/numbering/riwaya/tariq identity | Equal verse numbers do not prove boundary equality | More metadata for every caller; legacy bare references require explicit conversion at the boundary |
| Immutable read-only Qaloun adapter | Preserves text and source traceability without corpus duplication | Requires an authorized audited manifest and dependency availability |
| Execute unchanged hash-pinned mapper through a limited read-only dependency bridge | Reuses all graph/normalization/review logic without app startup or database access | Source-version-specific; hash drift requires review; eventually replace with a reviewed pure shared library |
| Versioned metadata first, SQLite for initial knowledge artifact | Local-first, read-mostly, small reviewed dataset without service operations | Adopt PostgreSQL for concurrent remote editorial workflows or deployment needs |
| Scholarly rule, detector, annotation, review and explanation are distinct | A source definition or machine candidate is not a verified occurrence | Stronger publication workflow and qualified review are required |
| Optional outbound providers and strict response admission | External outages cannot disable local tools; citations and compatibility survive normalization | Discovery and schema-specific adapters need maintenance |
| No RAG initially | Structured data and deterministic conditions meet initial needs | Reconsider only for authorized documentary semantic retrieval after evaluation |
| No agent/LLM/multi-agent workflow initially | A single MCP service and reusable domain services are sufficient | A future single Tadabbur consumer may be added without changing domain authority |
| Personal reading data stays in Wirdi AI | Limits access, credentials and user-data duplication | MCP receives only the minimum public passage/context query |
| Business contract v1.0 separate from MCP protocol and package 0.2.0 | Transport negotiation cannot express scientific or numbering semantics | Requires an explicit major-version compatibility policy |

## Dependency and source audit limits

The SDK package version and its v2 public API were verified against package
metadata, official documentation and local installed code. See the
[official SDK repository](https://github.com/modelcontextprotocol/python-sdk).
Runtime SDK and the development tools were installed in this project's `.venv`;
no heavyweight dataset, model or vector service was installed. Pydantic and dev
dependencies use bounded ranges rather than a full transitive deployment lock;
record tested versions and create a deployment lock when a deployment target is
chosen. Review upgrades with the real MCP smoke test.

External provider research distinguishes documentation and selected source
inspection from live protocol verification; see [PROVIDERS](PROVIDERS.md).
Publisher accuracy, sponsorship, source-count and license claims are not an
independent scientific or legal audit. No provider can confer Qaloun authority
through its name or a successful connection.

## Phase 2 refinements

The authorized read-only audit now confirms the original public 6,214-ayah
Qaloun JSON, its hashes, the verified 559-page metadata and the actual existing
resolver. See [SOURCE_AUDIT](SOURCE_AUDIT.md). No private database or application
runtime was opened and no sibling file was changed.

- Direct original-file reads avoid an independently maintained corpus and any
  PostgreSQL dependency. A small packaged metadata manifest pins identities,
  per-surah counts, raw/ordered-text/map hashes and authority source hashes.
- Phase 1's assumed Abu Nashit metadata was corrected before knowledge-tool
  publication: the current source identifies Qaloun but does not independently
  attest tariq. Actual references use `unspecified`; unsupported path requests
  fail. Future scholarly Tajwid scope remains Qaloun through Abu Nashit.
- The draft mapping schema was refined to preserve native statuses/ranges,
  components, context, notices and original attribution. Review-required output
  is diagnostic with `safe_for_source_retrieval=false`, never accepted retrieval
  evidence. Machine validation does not manufacture scholarly review IDs.
- The bridge compiles verified original bytes in isolated namespaces, binds only
  the observed read operations and never imports application startup, creates
  tables or writes sibling pyc files. Full original-audit conformance reduces
  adapter semantic risk; this remains a temporary compatibility boundary.
- Source files are revalidated every call. No automatic repinning, filesystem
  fallback, normalization of returned text, HTTP endpoint or app integration is
  included. Health remains lightweight and reports configuration only.
- No new runtime dependency was needed. SDK root-model output schemas preserve
  the success/error envelope directly without an unintended `result` wrapper.

The original foundation report remains historical. Current verification and
exact changed files are in [PHASE2_REPORT](PHASE2_REPORT.md).

## Phase 3 decisions (provider gateway, 0.3.0)

- **Request-scoped client sessions.** Each operation opens an official-SDK
  streamable-HTTP client, discovers tools, calls and closes. No long-lived session,
  background task or shared mutable connection; cancellation and timeouts close it.
- **Admission by schema signature.** A tool is callable only if it is in the audited
  catalog, annotated read-only and its canonical input/output schema hash equals the
  pinned sha256. Drift disables the tool; mutating or UI tools are never callable.
- **Narrow typed adapters, no passthrough.** Only Saadi tafsir search is exposed.
  Caller-supplied URLs, tool names and arguments do not exist.
- **Provider text is evidence, never corpus.** Hits carry provider, tool, response and
  excerpt digests, citation and `validation_status=unreviewed`; compatibility is
  `unknown` unless a mapped boundary check passed. Nothing is merged into Qaloun text.
- **Hafs boundary guard.** A scoped search first requires a safe mapping, then compares
  the provider's Hafs verse text with the local Hafs edition using the pinned mapper's
  own orthographic skeleton; any difference fails closed (`INCOMPATIBLE_RIWAYA`).
  Observed: `quran_mcp` passes for Qaloun 6:1-8; `tafsir_mcp` does not (orthography
  differs for 6 of 7 ayat), so it is limited to unscoped search. The guard was not loosened.
- **Passage tafsir fetch deferred.** Wirdi AI's Tadabbur flow fetches tafsir by passage;
  that tool is a Phase 6 decision, not part of Phase 3.
- **`quran_search_mcp` stays discovery-only** with an empty admitted-tool list.
- **No cache, no circuit breaker yet.** Both were designed in PROVIDERS and deferred
  until a licensing review permits retention.
- `tariq=unspecified` is unaffected: no provider can establish the corpus path.
