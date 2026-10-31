# Component architecture

Status: Local Tajwid candidates, 0.5.0. Business schemas are v1.0; transport
protocol negotiation is separate. Diagnostics, direct read-only Qaloun access,
existing-authority source mapping, a hash-pinned rule registry, deterministic candidate
detectors (`tajwid/`), a local page store and the Tajwid tools are operational. Every
rule and annotation is unreviewed; scholarly validation is not implemented.
See [SOURCE_AUDIT](SOURCE_AUDIT.md) for the read-only audit made before coding.

## Responsibilities and dependency direction

The server receives MCP requests and exposes approved local tools. It does not
act as an outbound MCP client and never queries a network service.

```mermaid
flowchart LR
    Transport[MCP stdio / future HTTP] --> Tools[Typed tool handlers]
    Tools --> Services[Domain services and admission policy]
    Services --> Quran[QalounDataReader]
    Services --> Mapping[SourceMappingAuthority]
    Services --> Tajwid[Rule registry and deterministic detectors]
    Services --> Repository[Knowledge repository]
    Services --> Admission[Local integrity and review gates]
    Admission --> Services
```

| Boundary | Owns | Must not own |
| --- | --- | --- |
| `server.py` | SDK lifecycle, registration and transport | Scholarly decisions, corpus rewriting |
| `tools/` | Parameter/result schemas and MCP error translation | Database queries or mapping algorithms |
| `domain/` | Reference/value contracts, future orchestration and read-only data port | FastAPI or mobile implementation details |
| `mapping/` | Pinned original mapper and narrow read-only dependency bridge | A second alignment algorithm |
| `quran/` | Metadata manifest, original public-file reads and exact text/page admission | Database startup or duplicate corpus |
| `tools/tajwid.py` | Tajwid tool registration, typed error translation | Scholarly approval or detector logic |
| `tajwid/` | Tokenizer with reversible offsets, detectors, engine and service | Scholarly approval; any LLM, RAG or network use |
| `knowledge/` package | Scholarly record models, hash-pinned `RuleRegistry`, local `PageStore` | Personal progress or user management |
| root `knowledge/` | `rules/` records and manifest, `sources/editions.json` metadata | Source books, extracted book text, a copied corpus |

A `validation/` module will be added when a named reviewer exists. There are no empty
modules pretending to work. A single `tools/contracts.py` captures the tool catalog. Structural guards currently
live beside their models; scientific validation remains a future service.

## Quran identity and immutable data

`QuranReference` requires `corpus_id`, `corpus_version`, `numbering_system`,
`riwaya`, `tariq`, `surah` and `ayah`. Unknown external metadata is represented
explicitly as unknown during quarantine; it cannot satisfy the Qaloun admission
gate. `QalounReference` restricts riwaya to `qaloun` and permits `unspecified` or
`abu_nashit` tariq. The audited active corpus accepts only `unspecified`; the
source metadata does not establish Abu Nashit.
These are application identifiers, not claims that all traditions fit one enum.

Pydantic enforces structural constraints (surah 1–114, strict positive integers
and bounded selection). The file adapter additionally enforces the pinned
manifest's actual per-surah limits, corpus/version, numbering and tariq.
Source hashes and structural checks establish machine integrity; scholarly
review remains a separate responsibility. Do not substitute Hafs limits, a
6,236-entry dataset, or a 604-page edition for Wirdi's manifest.

`QalounFileAdapter` reads the original public JSON transcription and verified
pagination directly from the explicitly configured Wirdi AI root. It rechecks
file and ordered-text checksums on each request, retains only process memory,
and makes no new on-disk corpus. Missing files fail without database access.
The metadata-only `quran/source_manifest.json` pins 6,214 Qaloun records, 6,236
internal Hafs records, all per-surah counts, source revision, map and evidence.
The current page metadata covers 559 printed pages, with 459 spanning ayat.
No word-level page splitting is available. Additional future corpus admission
will require an authorized manifest. The manifest must include edition,
riwaya/tariq, numbering identity, version, total and per-surah counts, page-map
version, licensing/attribution, text encoding, exact hash procedure, and a
trusted artifact digest. The 6,214-ayah count and 559-page map have now been checked against the original
public files and existing verification reports; those reports are not newly
performed scholarly or scan audits.

Hash exact UTF-8 text bytes with SHA-256 without Unicode normalization, trimming,
diacritic removal, punctuation replacement, or join/split rewriting. Hash the
whole source artifact separately. Retain individual ayat as separate records;
any display joining is a derived view. Verify artifact identity before admitting
it and record per-record digests. Hash equality proves byte consistency with a
trusted artifact; it does not prove scientific authenticity by itself.

Search may build normalized keys in separate fields with a named normalization
version. Those keys must never overwrite canonical text or determine boundary
mapping. Token/word spans bind to the original text hash and use zero-based,
half-open Unicode codepoint offsets. JavaScript consumers must convert to UTF-16
indices explicitly; one-based word indices are display aids, not primary keys.

## Mapping authority

`WirdiSourceMappingAdapter` implements the existing authority port. It reads
checksum-pinned `mapping.py`, `arabic.py` and `schemas.py` from Wirdi AI and
executes their unchanged source in isolated namespaces. A limited
`ReadOnlyAuthorityView` supplies only the edition lookup and two-predicate ayah
query used by that pinned resolver, over validated public records. It rejects
unsupported operations; there is no SQL engine, application import, database
startup, `commit`, credential access or sibling bytecode write.

This temporary bridge binds dependencies, not the boundary algorithm. Any code
hash drift disables mapping pending review. Conformance reproduces all 6,214
single-selection statuses and all 473 original unresolved reference/reason
records. A separately reviewed pure shared library remains the future preferred
interface; extraction is outside this task because Wirdi AI must remain untouched.

Requests name source selection and explicit target corpus/version/numbering.
Responses retain native statuses, components, source metadata, difference/context
notices, reasons and precise technical evidence, plus full target identities.
`mapping_requires_review` is returned as diagnostic data with
`safe_for_source_retrieval=false`; missing links produce no same-number fallback.
Verified equivalent/different statuses mean machine-checked passage boundaries,
not scholarly approval, recitation identity or word-level alignment.

The frozen Phase 1 draft mapping shape was refined before its first public tool
registration to represent native ranges/components and review semantics honestly.
No nonexistent scholarly validation IDs are invented. Span-level alignments are
unsupported; split/merge components keep complete source context explicitly.

## Storage choice

Begin Phase 4 with version-controlled, licensed source/rule metadata and an
optional **SQLite knowledge artifact** built offline after review. Do not create
tables in this phase. SQLite avoids a database service for a single Ubuntu
process, supports relational constraints and reproducible distribution, and
fits a small read-mostly knowledge set. Open published artifacts in `mode=ro`
and enable `query_only`; reserve `immutable=1` for artifacts truly guaranteed
immutable. Do not silently create an empty database when a path is missing.

| Choice | Initial value | Cost / upgrade trigger |
| --- | --- | --- |
| SQLite | Simple local operations, one distributable audited artifact | Concurrent editorial writers, remote review workflows and cross-host access require more coordination |
| PostgreSQL | Strong multiuser concurrency and server-managed roles | Extra service, credentials and migrations; adopt when concurrent scholarly editorial work or deployment scale requires it |

A repository boundary will isolate storage; avoid adding an ORM or PostgreSQL
driver until needed. Keep Wirdi AI's PostgreSQL and its personal reading records
in the original backend. Neither choice justifies copying the Quran corpus.

Planned entities: scholarly sources → editions → cited rule definitions;
conditions and exceptions reference rules; Quran references anchor passage
annotations; validation records bind approvals to exact subject versions and
hashes. Explanations cite both rule and annotation records. See
[TAJWID_ENGINE](TAJWID_ENGINE.md) for the publication gate.

## Reliability, security and observability

Execution remains stdio only: no listening socket, no database connection and no
private user input. Provider connections are outbound-only, opt-in, created per
operation and closed afterwards; a bearer credential, if ever needed, is read from a
configured environment variable name and never logged or returned. The only source
configuration is an absolute public-file root; no caller-provided file paths are accepted. `health_check` reports process-level
foundation readiness, not corpus integrity or scholarly validity. Its configured/unconfigured flags are not source-integrity claims. It returns no
paths, environment values, host inventory, or credentials. Python logging writes
to stderr; stdout belongs to MCP.

Future local handlers impose selection, context, response-size and deadline
limits. Source text is untrusted data, never instructions. No network origins,
credentials or caller-provided executable paths are accepted.

Retain only redacted request IDs, stable error codes and artifact versions as
operational metrics. Scholarly source retention requires a license-aware policy
when reviewed local knowledge is added.

Future Streamable HTTP must explicitly bind loopback during development and
add authentication, authorization scopes, origin/host validation, TLS at the
deployment boundary, rate limits and bounded sessions before shared deployment.
Read-only hints are descriptive metadata; the service must enforce permissions.

## Extension boundaries

Future `DocumentEvidenceRetriever.retrieve(query, source_ids, limit)` may return
licensed excerpts with edition/page/section, hashes, retrieval scores and
provenance. This is a conceptual port, deliberately not an installed module.
Qdrant and multilingual/Arabic embeddings are possible implementations only
after an evaluated documentary retrieval need. Similarity cannot approve a rule
or passage annotation, and retrieval failure must not affect deterministic tools.

A future single Tadabbur consumer may call only the versioned MCP catalog,
preserve claim-to-citation links and explicitly decline unsupported conclusions.
It receives structured candidates separately from verified results. No LLM,
agent framework, multi-agent system, vector store or embedding model is needed
for the current foundation.

Transport implementation follows the official SDK's
[server documentation](https://py.sdk.modelcontextprotocol.io/run/).
