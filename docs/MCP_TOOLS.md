# MCP tools — v1.0 business contract, Phase 2 release 0.2.0

Registered: `health_check`, `get_qaloun_passage`, `resolve_source_mapping`.
The other five catalog entries remain typed proposals and are not advertised.
`tools/contracts.py` supplies request and response models; implemented handlers
are in `tools/quran.py`. All registered tools are read-only and closed-world.

## Identity and shared result contracts

`selection` is `{start: QalounReference, end_ayah: integer}`: one surah, inclusive,
1–100 ayat, strict integral numbers, no inferred corpus or numbering. Nested
request models forbid unknown properties. The actual Qaloun corpus uses:

```json
{
  "corpus_id": "wirdi-ai:quranpedia:qalun",
  "corpus_version": "sha256:ece0a2b0efe44d496211c595d0a34f495413bc93f78fba8095a666e2048d1303",
  "numbering_system": "wirdi-ai:qalun-6214",
  "riwaya": "qaloun",
  "tariq": "unspecified",
  "surah": 6,
  "ayah": 1
}
```

The target is `wirdi-ai:quranpedia:hafs`, version
`sha256:0136b913aeb5a6a0389681f988215791ddd848c4347f7cf5e9d2574db7f1da49`,
numbering `wirdi-ai:qpc-hafs-6236`. Every request explicitly names its identity.
Abu Nashit is not independently attested by these files; requesting that tariq
returns `UNSUPPORTED_CONTEXT`. It remains a future scholarly scope, not an
assumed fact about this corpus. Actual per-surah counts are enforced by the
pinned manifest; Qaloun 2:286 is invalid even though Hafs 2:286 exists.

```text
Success[T] = {
  schema_version: "1.0", status: "ok", data: T,
  provenance: Provenance[1..], validation_status: ValidationStatus,
  warnings: string[]
}
Failure = {
  schema_version: "1.0", status: "error",
  error: {code: ErrorCode, message: string, retryable: boolean}
}
```

Both implemented data tools return this shape directly in MCP `structuredContent`
and a matching JSON text block, without an extra `result` wrapper. Domain failures
set `isError=true`. SDK structural-validation and unknown-tool errors retain
native MCP semantics and may not contain this envelope. Check `isError` first,
then `status`, then mapping admission flags; never treat review-required ranges
as safe simply because a mapping operation returned successfully.

`Provenance` names origin ID/version, exact artifact SHA-256 and citations.
`Citation` names source/edition, title, responsible party, publication/checkout,
locator, riwaya/tariq, status and version; URI is optional. Here these are original
corpus attribution and technical audit citations, not invented scholarly book
references. File hashes, ordered-text hashes and serialized page-array hashes
are distinct; see [SOURCE_AUDIT](SOURCE_AUDIT.md). Per-ayah hashes cover exact
UTF-8 text with no normalization.

`ValidationStatus` retains `unreviewed|machine_checked|scholarly_verified|rejected|not_applicable`.
Phase 2 emits only machine checks, unreviewed mapping outcomes and diagnostic
not-applicable status. No checksum or mapper result confers scholarly approval.

## Registered tools

| Tool | Required input | Output schema | Dependencies |
| --- | --- | --- | --- |
| `health_check` | None | `HealthReport` | None |
| `get_qaloun_passage` | `selection` | `PassageToolResponse`: `Success[Passage]` or `Failure` | Pinned Qaloun JSON, verified map and two pagination audit documents |
| `resolve_source_mapping` | `selection`, `target_corpus_id`, `target_corpus_version`, `target_numbering_system` | `MappingToolResponse`: `Success[SourceMapping]` or `Failure` | Pinned Qaloun/Hafs JSON, original mapper/normalizer/response types and correction audit |

The SDK derives schemas from typed handler parameters. Response root models keep
both success/error object schemas intact. Real stdio tests validate received
results against the schemas returned by `tools/list`.

### `health_check`

No inputs, source reads, paths or credentials. Reports the preserved
`status=foundation_ready`, service version, all three `available_tools`,
`quran_data`/`mapping` as `not_configured` or `configured_unchecked`,
`external_providers=disabled`, `tajwid_analysis=not_implemented`,
`validation_status=not_applicable`. A configured root is not a health assertion
about files; each data call performs its own admission checks.

### `get_qaloun_passage`

Required `selection`; no optional parameters. `Passage` returns the selection,
ordered `ayat`, source-file `snapshot_sha256`, full `corpus_text_sha256`,
`pagination_sha256`, pagination status and tariq-attestation limitation. Each ayah
has its full reference, untouched text, exact text digest, original provenance,
`page_start` and `page_end`. Returned whole ayat are never split across pages.
The envelope contains corpus and pagination provenance with technical citations.

Errors: `INVALID_REFERENCE` for corpus bounds/numbering, `UNSUPPORTED_VERSION`
for a different corpus/version, `UNSUPPORTED_CONTEXT` for unattested tariq,
`DATA_UNAVAILABLE` for missing configuration/unreadable files,
`INTEGRITY_FAILURE` for altered artifacts/text/page metadata. No normalization,
range clamping, alternate corpus, database or provider fallback. Mapping/Hafs
availability does not affect passage reads.

### `resolve_source_mapping`

Required inputs are listed above; no optional parameters. Only the audited
internal QPC Hafs target is supported. The exact existing resolver runs over a
narrow read-only bridge; no boundary algorithm is copied or approximated.

`SourceMapping` contains canonical `qaloun_reference`, full-identity target
`source_reference` ranges, native `mapping_status` and `mapping_type`, components,
`source_provenance`, notices, reasons, mapping method/version and artifact hash,
technical evidence, `validation_status` and `safe_for_source_retrieval`.
Components retain Qaloun/source ayah arrays, type, textual boundary verification
and context-outside-selection flags. Original source metadata and notices remain.

| Native status | Envelope validation | Safe for retrieval |
| --- | --- | --- |
| `verified_equivalent` | `machine_checked` | true |
| `verified_difference` | `machine_checked` | true, with difference/context notice |
| `mapping_requires_review` | `unreviewed` | false; any source ranges are candidates only |

Types include `exact`, `numbering`, `one_to_many`, `many_to_one`, `many_to_many`,
`mixed`, `missing`, `unverified`, `ambiguous`. Missing mappings have no invented
same-number target. Ambiguous many-to-many boundaries are never promoted.
Review-required mapping is a successful diagnostic result with an unsafe flag,
not a verified correspondence or a source-retrieval authorization.

Qaloun 6:1–8 maps to source 6:1–7; Qaloun 6:1 alone includes 6:2 as comparison
context. Qaloun 112:1 is equivalent. Qaloun 2:27 requires review. These are boundary
checks, not reading identity or word-level alignments. No Tafsir is fetched.

Errors: selection identity errors as above, unsupported target
`UNSUPPORTED_VERSION`, missing artifacts `DATA_UNAVAILABLE`, changed source or
authority code `INTEGRITY_FAILURE`. A source update requires a reviewed pin
change. No numeric fallback. Pagination is independent of mapping.

## Unregistered future tools

The following remain proposals with their Phase 1 typed contracts. They must not
be called or registered until their own data/review gates pass.

### `get_tajwid_rule`

Purpose: retrieve a published scholarly rule definition, not infer occurrences.
Required: `rule_id`, `version`. No optional parameters. `TajwidRule` contains
Arabic name, definition, Qaloun/Abu Nashit scope, cited conditions and exceptions,
evidence, validation status and validation record IDs. Public retrieval requires
approved scholarly records bound to that rule version; drafts stay in the
editorial workflow. `NOT_FOUND`, `UNVERIFIED_EVIDENCE`, `DATA_UNAVAILABLE` and
`UNSUPPORTED_VERSION` distinguish missing rules from inadmissible editions.

### `analyze_qaloun_tajwid`

Purpose: evaluate a bounded passage under an explicit reading context.
Required: `selection`, `reading_context` (`mode=wasl|waqf`; optional preceding and
following references and stop-after-word position). Optional: `rule_ids=[]`
means all supported published rules, `include_candidates=false`.

`Analysis` returns annotations, evaluated rule versions, limitations and coverage
(`partial|complete_for_requested_rules|unsupported`). Each annotation has its
stable ID, version, rule/version, text-bound anchor, context, detector version,
candidate/verified/rejected status, citations and review record IDs. Candidate
results never count as verified and are excluded by default. A context that
cannot be resolved returns `UNSUPPORTED_CONTEXT`; additional failures include
`INVALID_REFERENCE`, `DATA_UNAVAILABLE`, `INTEGRITY_FAILURE`,
`UNVERIFIED_EVIDENCE` and `NOT_FOUND` for unknown requested rules. No scientific
completeness claim is allowed beyond the specified supported rule versions.

### `get_tajwid_explanation`

Purpose: explain an already reviewed passage annotation. Required:
`annotation_id`, `annotation_version`. Optional: `language=ar` (only Arabic in
this draft). `Explanation` contains the annotation, rule, Arabic explanation,
and template version, with evidence in the records and response provenance.
Require scholarly approval of both rule and occurrence, plus a reviewed
explanation template. `NOT_FOUND`, `UNSUPPORTED_VERSION`,
`UNVERIFIED_EVIDENCE`, `UNSUPPORTED_CONTEXT` or `DATA_UNAVAILABLE` cause refusal.
Candidate annotations must not produce authoritative user-facing explanations.
The first implementation will use templates; no LLM dependency is planned here.

### `search_scholarly_sources`

Purpose: retrieve attributed evidence without generating an interpretation.
Required: `query` (1–1,000 characters), `category`
(`tafsir|linguistics|asbab_an_nuzul|qiraat|tajwid`). Optional: `selection=null`,
`provider_ids=[]` (policy-selected enabled providers), `limit=10` (1–20),
`cursor=null`. Passage-scoped searches require verified mapping before dispatch
to a provider with another numbering convention.

`SearchResults` includes hits, next cursor and `partial`. Each hit contains a
literal licensed excerpt, original source reference when applicable, citations,
provenance and compatibility (`unknown|mapped|audited_qaloun`). Broad documentary
search can return unknown compatibility as visibly unreviewed evidence; it
cannot attach that result as a verified Qaloun passage claim. Unattributed
results remain quarantined. Errors: `PROVIDER_UNAVAILABLE`, `PROVIDER_TIMEOUT`,
`SCHEMA_MISMATCH`, `INCOMPATIBLE_RIWAYA`, `UNVERIFIED_EVIDENCE`, mapping errors.
Valid no-match results differ from failed providers; partial failures appear in
warnings and must never be hidden by a successful fallback.

### `get_provider_capabilities`

Purpose: show configured/discovered capability metadata without claiming tools
were called. Optional: `provider_id=null` (all configured), `refresh=false`
(cached registry only). `refresh=true` explicitly permits discovery for enabled
providers, under service policy and deadlines; it does not call scholarly tools.
`Capabilities` returns providers and disabled provider IDs. Each capability
retains provider/tool IDs, original JSON schemas, schema digest, semantic
categories, evidence level and Qaloun compatibility. Errors: `NOT_FOUND`,
`PROVIDER_UNAVAILABLE`, `PROVIDER_TIMEOUT`, `SCHEMA_MISMATCH`. A disabled or
unreachable provider is never reported as an empty successfully discovered one.
This tool remains absent through Phase 2 because there is no implemented registry.

## Evolution and conformance

MCP negotiates protocol versions; Wirdi's `schema_version=1.0` versions business
meaning independently. Pin clients to compatible schema majors, use additive
optional fields for compatible changes, and publish a new major tool namespace
or negotiated catalog for breaking changes. Do not silently change numbering,
offset conventions, validation meaning, or default corpus version.

Future tool suites must independently test success, missing dependencies,
invalid references, integrity failure, provenance omission, unsupported contexts,
and error translation. Only tools whose dependencies pass admission checks may
be registered. No placeholder handler should return an empty verified analysis.
