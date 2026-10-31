# Phase 2 source audit and read-only interface

Audit date: 2026-10-30. Repository: the Wirdi AI checkout.
Inspection is read-only. No importer, application startup, migrations, database
connection, credentials or private tables were accessed. Existing reports are
evidence of the project's previous verification, not a new scholarly audit.

## Existing data architecture

`backend/app/content/importer.py` imports immutable public JSON transcriptions
into separate PostgreSQL `quran_editions` and `ayat` records. The authoritative
input for Qaloun is
`data/raw/quran-json/repo/data/quranpedia/qalun.json` (KFGQPC Qaloun via Qur'anpedia
mushaf 7, distributed by `risan/quran-json`). The internal comparison corpus is
`qpc-hafs.json` in the same directory. Both contain 114 surahs with contiguous
edition-specific `verse` IDs, exact `text`, and explicit `number_in_hafs` links.
They are the public inputs to the existing application, not a PostgreSQL export.

The source checkout reports revision
`6523a9ad3b73bb7e8cb3a9cdf0ea774b8bab3123`. No semantic corpus release is stored
in these files; the MCP contract uses the exact file SHA-256 as its version.
The current checkout's README mentions `meta/sources.json`, but that file is
absent. Do not invent a dump date/version. Preserve Qur'anpedia attribution and
the checkout revision/checksum. The existing importer records Qur'anpedia's
credit/dump-version terms, compilation CC BY-SA 4.0 and quran-meta MIT; this
audit does not newly clear redistribution of scans/fonts/books.

| Artifact | Observed identity |
| --- | --- |
| Qaloun JSON | 6,214 ayat; SHA-256 `ece0a2b0efe44d496211c595d0a34f495413bc93f78fba8095a666e2048d1303` |
| Qaloun ordered text | SHA-256 `0dcc85e8f92a7dd0ee22b7ec868418cf33a2686af176b7a995980626b02881b2` |
| QPC Hafs JSON | 6,236 ayat; SHA-256 `0136b913aeb5a6a0389681f988215791ddd848c4347f7cf5e9d2574db7f1da49` |
| Hafs ordered text | SHA-256 `b1cac65c40189bf28d607f83096e03b990c65147fbe4b67ccbb410d67552eb2e` |
| Verified pagination file | SHA-256 `d486070ee93363b0eed2a4514123a37b452168ee4a69edbd32253c44ec073395` |
| Pagination `verse_pages` array | SHA-256 `ca7aa4e4749c74bd08e07bb814b34b8cf876189a3c184df10bf23884264ccfc0` |

Ordered-text hashes use UTF-8 of texts in surah/verse order joined by one newline,
with no final newline, exactly as the importer. The page-array hash uses the
existing importer's `json.dumps(verse_pages).encode()` convention. Whole-file
hashes instead cover the original bytes; these distinct hash domains are named.

The numbering model is dataset-specific: e.g. Qaloun Al-Baqara has 285 ayat and
Al-An'am 167, whereas internal Hafs has 286 and 165. The Qaloun Fatiha has seven
numbered records but excludes the separate basmala from verse 1. Never substitute
Hafs counts, global database row IDs, or raw equal verse numbers.

Inspected source metadata explicitly identifies Qaloun from Nafi'; it does not
independently attest Abu Nashit. The active corpus therefore uses
`tariq=unspecified`. An Abu Nashit-specific claim/request cannot be certified
from this audit. Future Tajwid work still requires path-specific source review.

## Verified pagination

Use only `data/generated/qaloun_pagination_verified.json`, not the old
`qalun_pages.json`, raw Quranpedia page numbers, or a reused Warsh 604-page list.
The verified file names the King Fahd Complex 1427 AH **559 printed-page**
edition and contains 6,214 `[page_start, page_end]` pairs. Its existing evidence
is `docs/qaloun-pagination-validation.md` and `docs/day2-final-validation.md`.
The cited primary scan digest is
`17bb037d84f3e344c35122eb9fcad72d9b751d6011ab10dd896176f8974e8309`;
the scan itself is neither loaded nor redistributed by MCP.

There are 459 spanning ayat and no verified word-level page breaks. Return the
whole original ayah once with its start/end page metadata; do not split sacred
text to simulate printed fragments. The existing reader uses start-page
ownership, as documented in `docs/reader-corrections-report.md`.

## Existing mapper and validation semantics

Authority: `backend/app/tadabbur/mapping.py`, SHA-256
`1da0987ab721abe7f4843973f75e8b94c97c76f58f1f69dca094f5f51affdc66`.
Its `resolve(db, ayat, edition, surah)` follows explicit stored links, constructs
complete connected passages, checks order/contiguity and compares derived
orthographic skeletons exactly. `arabic.py` defines comparison normalization.
Neither routine changes returned/source Quran text. Fatiha basmala exclusion
is supported by complete-text comparison. Overlapping many-to-many components
require review even when their outer envelope matches.

The original statuses are `verified_equivalent`, `verified_difference` and
`mapping_requires_review`; types include exact, numbering, split/merge shapes,
mixed, missing, unverified and ambiguous. Components retain context outside the
selection, source ranges, reasons, notices and original edition provenance.
These are machine checks of boundaries, not scholarly verification or identical
recitation/word alignment. The existing single-selection audit records 3,076
equivalent, 2,665 different and 473 review-required selections.

Mandatory regression: Qaloun 6:1–8 → Hafs 6:1–7, with Qaloun 6:1–2 jointly
corresponding to Hafs 6:1. Qaloun 112:1 is an equivalent example. Qaloun 2:27 is
a real review-required example. Candidate source ranges on a review result must
never be used as admitted scholarly retrieval references.

## Safest reusable interface, selected before implementation

Read the original public JSON/map files directly using binary read-only opens,
with trusted checksums stored in a small metadata-only MCP manifest. Parse the
same bytes that were hashed; retain only process memory, not another corpus on
disk. Revalidate each request so later source changes fail closed. A missing
Hafs file or mapper must not prevent independent Qaloun passage reads.

Reuse the exact pinned mapper source, without copying/reimplementing its graph,
normalization, basmala, ambiguity or boundary logic. Bind only its narrow
`get(QuranEdition, id)` / `scalars(select(Ayah).where(edition_id, surah))` read
interface to validated public records. The bridge is not a SQL engine; it accepts
only the two observed equality predicates and rejects everything else. Bind the
original response types from the pinned `schemas.py` and normalization from
the pinned `arabic.py`. Execute verified source bytes in isolated namespaces
without importing `app`, `db`, `models`, the importer or FastAPI. Compilation
must not write sibling `__pycache__` files. No SQLAlchemy or database is needed.

This temporary compatibility bridge is deliberately source-version-specific.
All three authority files are hash-pinned; drift disables mapping pending review.
Conformance tests must compare the complete 6,214-selection result with the
existing audit, plus focused golden boundary and malformed-input cases. The
preferred eventual interface remains a separately reviewed pure shared library;
extracting one would modify Wirdi AI and is outside this authorization.

MCP returns native review semantics and explicit `safe_for_source_retrieval`.
Review-required output is useful diagnostic data, never an accepted
correspondence. No numeric or approximate fallback is permitted. Technical
citations point to the existing corpus records and audit locators; no new
scholarly references are fabricated. No external source retrieval occurs.

## Bundled snapshot, 2026-10-31

The files below are now shipped in `src/wirdi_mcp/quran/snapshot/` so the project runs without a
Wirdi AI checkout. Six are byte-identical to the originals (same hashes as above); `schemas.py` is
trimmed and the three audit documents are replaced by short public notes, each with its own hash in
the `bundled` section of the manifest. With `WIRDI_AI_ROOT` set, the original hashes are checked.

## Controlled manifest update, 2026-10-31

Two pinned authority files in the Wirdi AI checkout had drifted since the audit:

| File | Previous SHA-256 | Current SHA-256 |
| --- | --- | --- |
| `backend/app/tadabbur/arabic.py` | `abe3e8f8dfa01333e4f7156b5f8ade0e4aa73b8d995bf1ced7b8e614910f4ffc` | `d3e6bb992cb5398fff534aba1f05d12d3b1984f8fca6e14a46fc0ea3943919b7` |
| `backend/app/schemas.py` | `512a833186853d7ee0026ce5ef2672e21d74a63fb5707f4d48953d1200761108` | `c4cdec8706d33f2a947efcf79f00b381bfb539102fc219f93041cdaef4c3f1a7` |

The Wirdi AI checkout has no git metadata, so the files could not be diffed. The
update was admitted functionally, not by inspection: with only these two hashes
changed, the complete real-source suite (`WIRDI_TEST_SOURCE_ROOT` set) passed,
including the 6,214-selection single-ayah conformance against the existing mapping
audit and all golden boundary cases (46 passed, 0 failed). Every other pinned hash
(Qaloun and Hafs text, pagination, `mapping.py`, audit documents) was unchanged.
The check itself was not relaxed. Only `mapping/adapter.py` reads these two files;
passage reads were never affected. Any future drift fails closed again.
