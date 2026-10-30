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

Current state: **Phase 2 complete**, subject to the source limitations in
[SOURCE_AUDIT](SOURCE_AUDIT.md). Direct read-only Qaloun access, source integrity,
559-page metadata and original resolver reuse are implemented. Real stdio
calls and complete source-audit conformance have passed. No application/database
integration, external provider, knowledge database, Tajwid engine, RAG or agent
was added. [PHASE2_REPORT](PHASE2_REPORT.md) records exact verification.

## Next milestone: Phase 3 optional external MCP gateway

1. Review pinned provider release/endpoint and content permissions.
2. Implement opt-in discovery with original schemas and capability admission.
3. Add provider-specific normalization retaining original scholarly references.
4. Require safe source mapping before passage-specific external retrieval.
5. Add bounded deadlines, retry/fallback, schema drift and failure-isolation tests.
6. Record actual discovery/tool calls before claiming live provider verification.

Keep providers disabled until that separate milestone. The current task stops
at Phase 2. Path-specific Tajwid requires an independent Abu Nashit source audit;
the current corpus's tariq remains unspecified. A preferred pure shared mapper
library extraction would require a separate authorized change to Wirdi AI.
