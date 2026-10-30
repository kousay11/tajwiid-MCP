# Incremental implementation roadmap

Each phase has an explicit admission gate. Tool availability follows actual
verified dependencies, not the presence of a schema or a planned module.

| Phase | Scope | Completion gate |
| --- | --- | --- |
| 1 — Foundation | Python packaging, pinned official MCP SDK, environment configuration, stderr logging, stdio server, safe diagnostic, typed future contracts and architecture | Unit tests, real local MCP protocol smoke test and packaging/lint checks pass; exactly one diagnostic is advertised |
| 2 — Quran tools | Agree on manifest/reference contract, read-only Qaloun access, existing mapping authority adapter, source metadata and provenance | Owner-authorized corpus audit, exact-byte integrity tests, per-surah/page-map checks, shared mapper conformance fixtures and rejection of ambiguity; then register passage/mapping tools |
| 3 — External gateway | Optional provider adapters, discovery registry, normalized evidence, timeouts/retries/fallback and compatibility admission | Pinned provider sources, licensing review, opt-in real discovery/call records, offline failure tests, schema drift detection and local-tools-survive-outage tests |
| 4 — Tajwid knowledge | Scholarly source/edition audit, licensing, review records, conditions/exceptions and first reviewed rules | Qualified scholarly approval scoped to Qaloun/Abu Nashit; reproducible versioned knowledge artifact; only then expose published rule retrieval |
| 5 — Tajwid engine | Deterministic detection, context and exception handling, candidates, reviewed passage annotations and Arabic explanations | Rule-specific positive/negative/exception fixtures, Wasl/Waqf and boundary tests, scholar-labeled evaluation, explicit coverage and approval gates; then expose analysis/explanations |
| 6 — Wirdi AI integration | Backend lifespan client, feature flags, Tadabbur integration, UI compatibility and migration | Existing Quran.ai path preserved, mapping conformance and corpus integrity unchanged, failure isolation/privacy tests, regression tests and rollback exercised |
| 7 — Optional expansion | A single agent, grounded LLM explanations or documentary RAG only if justified | Evaluated user need, authorized sources, citation correctness/refusal tests, Arabic evaluation and reproducible quality/latency/cost benchmarks |

Current state: **Phase 3 implemented (0.3.0)** on top of Phase 2, subject to the
limits in [PHASE3_REPORT](PHASE3_REPORT.md) and [SOURCE_AUDIT](SOURCE_AUDIT.md). Direct
read-only Qaloun access, source integrity, 559-page metadata and original resolver
reuse (Phase 2) are unchanged. Phase 3 adds a disabled-by-default outbound gateway with
two tools. No application/database integration, knowledge database, Tajwid engine, RAG
or agent was added.

## Phase 3 status: optional external MCP gateway

| Item | State |
| --- | --- |
| Pinned provider endpoints and content-permission review | Endpoints pinned in `providers/catalog.json`; licensing questions open (see PROVIDERS) |
| Opt-in discovery with original schemas and capability admission | Done; sha256 schema-signature admission, read-only annotation required |
| Provider-specific normalization keeping scholarly references | Done for `quran_mcp` and `tafsir_mcp` (Saadi tafsir search only) |
| Safe source mapping before passage-specific retrieval | Done; unsafe mapping rejected before any network use |
| Deadlines, retry, fallback, drift and failure isolation tests | Done with mocked peers |
| Recorded real discovery and calls | Done; see `docs/provider-evidence/` |
| Passage tafsir *fetch* tool, circuit breaker, caching | Not implemented; deferred |

`quran_search_mcp` is discovery-only. Path-specific Tajwid still requires an independent
Abu Nashit source audit; the current corpus's tariq remains `unspecified`. A preferred
pure shared mapper library extraction would require a separate authorized change to Wirdi AI.
