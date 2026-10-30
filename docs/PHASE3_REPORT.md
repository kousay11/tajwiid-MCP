# Phase 3 report — optional external provider gateway (0.3.0)

Date: 2026-10-30. Scope: close-out of the gateway that Codex built, with verification,
hardening and documentation. No new providers or tools were added; Wirdi AI, the Quran
corpus, pagination, mapping and `tariq=unspecified` were not touched.

## What Phase 3 is

Two additional read-only tools on the existing stdio server, backed by `src/wirdi_mcp/providers/`:

- `get_provider_capabilities` — provider state; `refresh=true` performs MCP discovery.
- `search_scholarly_sources` — Saadi tafsir search with attributed, `unreviewed` hits.

Providers are disabled by default and enabled only by an administrator file
(`WIRDI_MCP_PROVIDER_CONFIG`, template `providers.example.json`). Endpoints and admitted
tools are pinned in `providers/catalog.json`; a tool is callable only when its live schema
hash equals the pinned sha256 and it is annotated read-only. External text never becomes
Qaloun text and never makes a transmission-path claim. See [MCP_TOOLS](MCP_TOOLS.md),
[PROVIDERS](PROVIDERS.md) and [DECISIONS](DECISIONS.md).

## Starting state

Codex had implemented the gateway, adapters, catalog, tools and 18+ mocked tests (the folder
had no git history). It had not updated any documentation, written a report, built a wheel,
or run the live pytest suite. The code was preserved; this session changed only the items below.
A baseline commit (`7a9bd92`) captured the state before any edit. Before committing, the file set was
scanned for secrets, credentials, local configuration and generated files: none found
(`.venv`, `dist`, caches, `.verification`, `.env` are git-ignored; the evidence file holds
schemas, digests and query arguments only).

## Changes made

| Area | Change |
| --- | --- |
| `src/wirdi_mcp/mapping/bridge.py`, `providers/gateway.py` | The mapper's `skeleton` is obtained through a named accessor `pinned_skeleton()` instead of an inline `__globals__` lookup (behavior identical) |
| `src/wirdi_mcp/tools/contracts.py` | `ProviderCapabilitiesInput.provider_id` now uses the same `ProviderId` type as the registered tool |
| `src/wirdi_mcp/server.py`, `pyproject.toml` | Formatting fix; `.verification` excluded from ruff |
| `tests/unit/test_provider_transport.py` (new) | 13 offline tests: compression, declared and streamed oversize bodies, redirects, missing credential, HTTP status classification, tool-error handling, non-JSON, tool admission |
| `tests/unit/test_provider_gateway.py` | +20 offline cases: config validation, request validation, discovery-only provider never called, disabled provider, read-only/absent admitted tool, rate-limit retry, auth failure not retried, tafsir_mcp scoped success/failure, attribution mismatch, source-namespace mismatch, empty result |
| `scripts/record_provider_evidence.py` (new) | Opt-in LIVE recorder; writes digests and outcomes, never excerpts |
| `docs/` | README, ROADMAP, PROVIDERS, MCP_TOOLS, ARCHITECTURE, DECISIONS, INTEGRATION, PHASE2_REPORT pointer synced; this report added |
| `docs/provider-evidence/` | `2026-10-30-live-gateway.json` (this session), `2026-10-30-codex-gateway-live-summary.json` (Codex's run summary) added next to Codex's `2026-10-30.json` |

Not changed: `SOURCE_AUDIT.md`, `src/wirdi_mcp/quran/*`, `catalog.json`, `providers/adapters.py`,
`providers/transport.py`, `providers/models.py`, anything in Wirdi AI.

## Verification actually run

All commands from `/home/najjar/Documents/Me/wirdi-mcp`; pytest with `-p no:cacheprovider`.

| Category | Command | Result |
| --- | --- | --- |
| Lint | `ruff check .`, `ruff format --check .`, `pip check` | clean |
| Offline (mocked peers, local stdio; no internet, no source files) | `pytest` | **80 passed, 21 skipped** |
| Offline + real-source (read-only Wirdi AI files, mocked peers) | `WIRDI_TEST_SOURCE_ROOT=…/wirdi-Ai pytest` | **96 passed, 5 skipped** (the 5 are the live tests) |
| Live providers (contacts real hosted servers) | `WIRDI_TEST_LIVE_PROVIDERS=1 pytest tests/integration/test_live_providers.py` | **5 passed, 0 skipped** at 2026-10-30T20:25+01:00 |
| Live gateway evidence | `scripts/record_provider_evidence.py` | see below |
| Real stdio smoke | `scripts/verify_local.py` | 5 tools, `0.3.0`, corpus sha256 `ece0a2b0…`, 6:1-8 → Hafs 6:1-7 `verified_difference` |
| Wheel | `hatchling build -t wheel`, installed in an isolated venv, stdio smoke | `dist/wirdi_mcp-0.3.0-py3-none-any.whl`, sha256 `65f87cc2…af7`; 5 tools, providers disabled by default |

Phase 2 tests: 45 originally; all still pass (the 96 includes them). Mocked results are not
counted as live verification anywhere in this report.

### Integrity

- The 11 Wirdi AI files in the pinned manifest plus the transmission audit were hashed before and after the work: **0 changed**, and none differs from the manifest.
- `src/wirdi_mcp/quran/` and `source_manifest.json` are unchanged from the baseline commit.
- Review-required mapping (Baqara 2:27) is rejected with `AMBIGUOUS_MAPPING` before any network use, in tests and live.
- `tariq=unspecified` remains in the server instructions, manifest and tool outputs.

## Provider verification status

Live contact on 2026-10-30 (HTTP 200 on initialize for all three; SDK discovery succeeded):

| Provider | Discovery | Admitted tools match pinned signatures | Broad search | Scoped Qaloun 6:1-8 | Review-required 2:27 |
| --- | --- | --- | --- | --- | --- |
| `quran_mcp` | ready, 36 tools | yes | 2 hits, `unknown` compatibility | 2 hits, `mapped_boundaries_checked` | `AMBIGUOUS_MAPPING`, no network |
| `tafsir_mcp` | ready, 17 tools | yes | 2 hits, `unknown` compatibility | **refused: `INCOMPATIBLE_RIWAYA`** | `AMBIGUOUS_MAPPING`, no network |
| `quran_search_mcp` | ready, 8 tools | n/a (none admitted) | not supported by design | not supported | n/a |

### Finding: Tafsir MCP fails the scoped boundary check

The plan assumed Tafsir MCP scoped search would work. It does not. Comparing the provider's
`fetch_ayah` text for 6:1-7 against the local Hafs edition with the pinned mapper's
orthographic skeleton, only 6:2 is equal; 6:1 and 6:3-7 differ in letter-level
orthography (e.g. alef/waw/hamza placement). The gateway correctly fails closed. The guard
was not loosened and the scope was not changed. Consequence: `tafsir_mcp` serves unscoped
search only, and the scoped success path is covered by mocked tests but has no live
success. Whether the orthographic differences are acceptable is a scholarly decision for the owner.

### Not verified live

- A successful scoped search through `tafsir_mcp`.
- Rate-limit retry, timeout, schema drift and malformed-payload behavior against real servers (mocked only).
- Authentication (neither provider needs it; the credential path is mocked).
- Any `quran_search_mcp` tool call by the gateway (no tool is admitted).
- Scholarly accuracy of any returned excerpt, or the publication edition behind it.

## Evidence retained and withheld

`docs/provider-evidence/` keeps tool names, annotations, original schemas, call arguments,
response/excerpt digests and outcomes. The raw response bodies recorded by Codex in the
git-ignored `.verification/phase3/*-calls.json` contain provider tafsir and Quran text and were
**not** copied into the repository, because data licensing is unresolved (see PROVIDERS).
They remain locally in `.verification/`.

## Remaining limitations

1. Only Saadi tafsir search; no passage-tafsir fetch (Wirdi AI's Tadabbur flow needs one; Phase 6 decision).
2. No Qaloun or Abu Nashit text from any provider; all hits are `unreviewed`, edition unverified, excerpts possibly truncated.
3. `tafsir_mcp` cannot pass the scoped boundary check for the tested passage.
4. No cache and no circuit breaker (designed, deferred).
5. Licensing/terms questions are open: Quran MCP (QFGPL non-commercial software; hosted-service terms not found), Tafsir MCP (CC BY 4.0 data license conflicts with a commercial-redistribution caveat), and retention of excerpts in Wirdi AI. Resolve before any public or commercial release.
6. `catalog.json` hashes pin schemas, not dataset versions (`dataset_version` is null); content can change silently.
7. Wirdi AI does not use Wirdi MCP yet; it keeps its own quran.ai client (Phase 6).
8. Live tests depend on third-party servers and are skipped on outage; mocked peers do not prove protocol behavior.
9. The Abu Nashit transmission path remains unestablished for the corpus ([audit](../../wirdi-Ai/docs/qaloun-transmission-path-audit.md): PARTIALLY CONFIRMED); path-specific Tajwid (Phase 4+) is blocked on that.
