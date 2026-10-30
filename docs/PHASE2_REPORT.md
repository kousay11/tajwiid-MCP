# Phase 2 delivery report

Completed 2026-10-30. Package: `wirdi-mcp==0.2.0`; business schemas: v1.0.
Scope: verified read-only public Quran access and original source mapping only.

## Implemented architecture

The server preserves stdio operation, safe logging, configuration validation and
the Phase 1 diagnostic. It now registers exactly three read-only tools:

| Tool | Request | Response |
| --- | --- | --- |
| `health_check` | No parameters | `HealthReport`; configuration only, no source reads |
| `get_qaloun_passage` | `selection: PassageSelection` | `PassageToolResponse`: `Success[Passage]` or `Failure` |
| `resolve_source_mapping` | Selection plus explicit target corpus/version/numbering | `MappingToolResponse`: `Success[SourceMapping]` or `Failure` |

The SDK publishes typed input/output schemas through `tools/list`. Both data
tools return the success/error envelope directly in `structuredContent`, with
matching JSON text. Domain failures set `isError=true`; SDK argument/unknown-tool
errors retain their native behavior. No Tajwid or provider tools are registered.

`PublicSourceRepository` verifies original file bytes against the packaged
metadata-only manifest, actual counts and ordered-text checksums. The adapter
returns original strings unchanged, per-ayah UTF-8 SHA-256, original attribution,
whole-ayah page spans and corpus/pagination identities. Every request rechecks
source bytes. It creates no database, corpus copy or on-disk cache. All temporary
test datasets contain non-Quran sentinels, never copied sacred text.

`WirdiSourceMappingAdapter` invokes the existing checksum-pinned resolver
unchanged. `mapping/bridge.py` binds its observed edition lookup and two-predicate
ayah read interface to validated public records. The original mapper,
normalizer and response types are compiled from verified bytes in isolated
namespaces. There is no application/database startup, SQLAlchemy installation,
private-table access, importer call or sibling bytecode write. The bridge is a
temporary source-version-specific compatibility interface; a future separately
reviewed pure shared package remains preferable. No mapping algorithm was
rewritten or approximated.

The [source audit](SOURCE_AUDIT.md) was written before adapter implementation.
It documents existing storage, data provenance, pagination and the selected
read-only interface. Further architecture details are in
[ARCHITECTURE](ARCHITECTURE.md), schemas in [MCP_TOOLS](MCP_TOOLS.md).

## Source identity

Original root: `/home/najjar/Documents/Me/wirdi-Ai` (explicit configuration,
not an automatically searched location). Inputs:

- `data/raw/quran-json/repo/data/quranpedia/qalun.json`: 114 surahs, 6,214 ayat.
  Raw SHA-256 `ece0a2b0efe44d496211c595d0a34f495413bc93f78fba8095a666e2048d1303`;
  ordered-text SHA-256 `0dcc85e8f92a7dd0ee22b7ec868418cf33a2686af176b7a995980626b02881b2`.
- `data/raw/quran-json/repo/data/quranpedia/qpc-hafs.json`: 6,236 internal target
  ayat; raw SHA-256 `0136b913aeb5a6a0389681f988215791ddd848c4347f7cf5e9d2574db7f1da49`.
- `data/generated/qaloun_pagination_verified.json`: 559-page King Fahd Complex
  1427 AH edition; raw file SHA-256
  `d486070ee93363b0eed2a4514123a37b452168ee4a69edbd32253c44ec073395`;
  existing page-array SHA-256
  `ca7aa4e4749c74bd08e07bb814b34b8cf876189a3c184df10bf23884264ccfc0`.

Qaloun identity is `wirdi-ai:quranpedia:qalun`, version `sha256:<raw-file-hash>`,
numbering `wirdi-ai:qalun-6214`. The internal target uses
`wirdi-ai:quranpedia:hafs` and `wirdi-ai:qpc-hafs-6236`. Source checkout revision
is recorded in the manifest; no semantic release or missing dump date was
invented. No snapshot was necessary: reads use the existing original files.

**Transmission limitation:** inspected metadata identifies Qaloun, but does not
independently attest Abu Nashit. Active references use `tariq=unspecified`;
requests claiming another path are rejected. This corrects a Phase 1 draft
assumption before knowledge-tool publication. No path-specific Tajwid claim
is possible from this audit.

## Mapping behavior and limits

- Qaloun 6:1–8 maps to source/Hafs 6:1–7; Qaloun 6:1–2 jointly correspond to 6:1.
- Qaloun 112:1 is `verified_equivalent` / `exact`.
- Numbering-only changes, splits, merges and source context beyond a partial
  selection retain the original components and notices. Fatiha basmala exclusion
  remains the original text-supported behavior.
- Native `verified_equivalent` and `verified_difference` mean machine-checked
  boundaries with `safe_for_source_retrieval=true`, not scholarly certification,
  identical recitation or word alignment.
- Native `mapping_requires_review` returns diagnostic data, `unreviewed` status
  and `safe_for_source_retrieval=false`. Candidate ranges remain marked unsafe;
  missing links never produce a numeric fallback. Ambiguous many-to-many
  allocations remain unresolved. No Tafsir/source call occurs here.
- Corpus, numbering, target-version, text, map and authority-code mismatches
  fail closed. Missing configuration/artifacts produce typed unavailability.
  The health diagnostic remains available. Qaloun reads need neither Hafs nor
  mapping code; boundary mapping needs no page map.
- Pagination has 459 spanning ayat and no verified word-level break offsets.
  Results contain complete unchanged ayat with start/end metadata.

## Verification results

| Check | Result |
| --- | --- |
| Full opted-in offline suite | **45 passed** in 10.12 seconds |
| Default independent suite | **30 passed, 15 skipped**; skips are explicitly opt-in public-source checks |
| Full original mapping-audit conformance | All 6,214 selections evaluated; 3,076 equivalent, 2,665 differing, 473 review-required; all original unresolved source ranges and reasons match |
| Original text | Every returned Qaloun string compared with the original JSON across all 6,214 ayat |
| Identity/integrity failures | Wrong IDs/versions/numbering/tariq, invalid Qaloun bounds, raw artifact changes, ordered-text hash and pagination metadata checks passed |
| Mapping regressions | Al-An'am, equivalent, numbering, split/merge, outside-selection context, missing/invalid links, real unverified case and synthetic ambiguity passed |
| Real stdio | Discovery, schemas, both new calls, review outcome, typed errors, health and Tajwid unavailability passed |
| No data mutation | Ten audited source/code/evidence files retain original hashes, sizes and modification times; reader tests also compare complete synthetic file bytes/mtimes |
| Local verification script | Passed; service 0.2.0, 8 canonical ayat, source 6:1–7, machine-checked difference |
| Ruff lint and formatting | Passed |
| Dependency consistency | `pip check`: no broken requirements |
| Compilation | `compileall` on MCP source/tests/script passed |
| Wheel | Built 0.2.0, includes 21 package files, metadata-only manifest and console entry point |

Stdio tests and the verification script ran outside the execution sandbox's known
subprocess-I/O restriction. Source audit/reads were already permitted inside the
sandbox; no filesystem restriction was bypassed. Tests never opened a database
or connected to an external MCP server. No Wirdi AI test suite, importer or
migration was executed.

An initial test expected an invalid disjoint-link case to be `unverified`; the
unchanged resolver correctly classified it as `ambiguous`, and the expectation
was corrected. Initial SDK union output acquired a `result` wrapper; typed root
models corrected the published direct envelope and real stdio checks then passed.
No authority logic or source data was changed to make tests pass.

## Local setup and verification

```bash
python3 -m venv .venv  # only if not already created
.venv/bin/python -m pip install -e '.[dev]'
export WIRDI_AI_ROOT=/home/najjar/Documents/Me/wirdi-Ai
.venv/bin/wirdi-mcp
```

The last command waits for MCP input. For actual client calls instead:

```bash
.venv/bin/python scripts/verify_local.py --source-root /home/najjar/Documents/Me/wirdi-Ai
WIRDI_TEST_SOURCE_ROOT=/home/najjar/Documents/Me/wirdi-Ai .venv/bin/python -m pytest -q
env -u WIRDI_TEST_SOURCE_ROOT .venv/bin/python -m pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python -m pip check
.venv/bin/python -m compileall -q src tests scripts
.venv/bin/python -m hatchling build -t wheel
```

These verification commands were executed. The existing `.venv` was refreshed
with `pip --no-cache-dir install -e '.[dev]'`; no new runtime dependency was
needed. Hatchling is now declared in the development extra so the documented
build command works in a fresh development installation. No source dataset,
PostgreSQL dump, model, vector service or provider package was installed.

`WIRDI_AI_ROOT` must be absolute. `.env` is never automatically loaded; use the
explicit shell-loading instructions in the README or an MCP host's environment
configuration. Unconfigured tools return `DATA_UNAVAILABLE`; no source root is
guessed. Changed pinned artifacts require a reviewed manifest update, not an
automatic checksum refresh. Per-call file admission fails on unreadable paths.

## Exact authored files changed

18 existing files modified:

```text
.env.example
.gitignore
README.md
pyproject.toml
docs/ARCHITECTURE.md
docs/DECISIONS.md
docs/INTEGRATION.md
docs/MCP_TOOLS.md
docs/ROADMAP.md
src/wirdi_mcp/__init__.py
src/wirdi_mcp/config.py
src/wirdi_mcp/server.py
src/wirdi_mcp/domain/models.py
src/wirdi_mcp/domain/ports.py
src/wirdi_mcp/mapping/adapter.py
src/wirdi_mcp/tools/contracts.py
src/wirdi_mcp/tools/diagnostics.py
tests/integration/test_stdio.py
```

14 files created:

```text
docs/SOURCE_AUDIT.md
docs/PHASE2_REPORT.md
scripts/verify_local.py
src/wirdi_mcp/domain/exceptions.py
src/wirdi_mcp/mapping/bridge.py
src/wirdi_mcp/quran/__init__.py
src/wirdi_mcp/quran/source.py
src/wirdi_mcp/quran/source_manifest.json
src/wirdi_mcp/tools/quran.py
tests/conftest.py
tests/integration/test_phase2_stdio.py
tests/integration/test_source_authority.py
tests/unit/test_mapping_bridge.py
tests/unit/test_quran_access.py
```

Generated/ignored artifacts: refreshed `.venv`, caches/bytecode, the 0.2.0 wheel,
and `.verification/` metadata-only before/after hash inventories. No files in
Wirdi AI were edited, deleted, migrated or overwritten. The original Phase 1
completion report and future Tajwid/provider documentation remain historical or
planned; no corresponding feature was implemented.

## Next milestone

Phase 3: optional external MCP discovery, capability admission, response/source
normalization, deadlines and fallback, while requiring safe mapping for
passage-scoped retrieval. It was started afterwards; see
[PHASE3_REPORT](PHASE3_REPORT.md). Wirdi AI backend integration,
Tajwid, RAG and agents remain deferred to their roadmap gates.
