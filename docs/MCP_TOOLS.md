# MCP tools: local Tajwid candidates (0.6.0)

The stdio server exposes twelve read-only tools. There is no outbound MCP client, HTTP
provider, network fallback or external scholarly search. All tools use closed-world
contracts and return structured success or error envelopes. Contracts are in
`src/wirdi_mcp/tools/contracts.py` (`TOOL_CONTRACTS`); registration is in
`tools/quran.py` and `tools/tajwid.py`.

| Tool | Purpose |
| --- | --- |
| `health_check` | Readiness and configuration only |
| `get_qaloun_passage` | Unchanged Qaloun ayat with verified 559-page spans |
| `resolve_source_mapping` | The existing pinned mapping authority; review-required results are unsafe for retrieval |
| `list_tajwid_rules` | Rules available locally, with family, detectability and whether a detector exists |
| `get_tajwid_rule` | One rule record with conditions, exceptions, limitations and book and page citations |
| `analyze_qaloun_tajwid` | Candidate occurrences for 1 to 100 ayat; filters `rule_ids` and `families`; paged |
| `summarize_tajwid` | Per-rule counts for a surah or ayah range (at most 300 ayat) with paged per-ayah counts |
| `analyze_app_page` | Candidates for the ayat that begin on a page (1 to 559) of the verified Qaloun layout |
| `list_reading_combinations` | For each ayah with a madd or a plural meem, the readings that may be taken together (Nabhan pp.98-108); see below |
| `get_source_page` | 1 to 5 pages of a locally placed source book (printed page numbers) |
| `search_source_pages` | Literal, lossy-normalized Arabic search over local pages; returns page hits |
| `get_letter_properties` | Static place of articulation and characteristics for 1 to 29 base letters (Book A pp.40-45); an entry that is not one base letter is `INVALID_REFERENCE` |

## What an annotation is

Every served annotation has `status: "candidate"`: a deterministic procedure proposed it, and
no reviewer confirmed it. Each carries the rule and version, a `TextAnchor` (ayah SHA-256,
half-open codepoint range into the unchanged ayah text, word index), the reading context,
the detector version, `evidence` (book and page citations of the rule), `page_refs` (the
application's 559-page span of the ayah), an occurrence `note` and `variants`: the readings
the source permits for that occurrence (for example 2, 3 or 4 harakat for a separated madd,
or sukun versus a sila for a plural meem). The engine never picks one of them. The other statuses are `unsupported_context`, `rejected` and
`scholarly_verified`, which is reserved and never emitted (`EMITTABLE_STATUSES`).

## Rule families

`families` filters `analyze_qaloun_tajwid`, `summarize_tajwid` and `analyze_app_page`:
`madd` (23 rules), `hamza` (19), `tafkhim_tarqiq` (12), `imala_taqlil` (2), `idgham_general` (5),
`ya_idafa` (6) and the first-release families (`qalqala`, `noon_sakina_tanween`, `mim_sakina`,
`ghunna`, `lam_taarif`). Two hamza rules have a
record but no detector (`has_detector: false` in `list_tajwid_rules`). Book A coverage is in
[BOOK_A_COVERAGE](BOOK_A_COVERAGE.md); a request for each family is in
[TESTING_GUIDE](TESTING_GUIDE.md).

## Reading context

`reading_context.mode` is `waqf` (reading stops at the end of each selected ayah, tanween
and a final noon are dropped, a final qalqala letter is evaluated at the stop) or `wasl`
(continuous reading across the selected ayat). In `wasl`, the last ayah's final position
needs the following ayah: pass it as `following` (must be the next ayah of the same
surah) or the position is reported under `unresolved` and the coverage becomes `partial`.
`stop_after_word` ends the last ayah after that word. Waqf signs inside an ayah are not
stops. `preceding` is accepted but no implemented rule uses it. The reading context is
never inferred from punctuation.

## Result semantics

- `coverage` is `complete_for_requested_rules` only when no position was left unresolved;
  it never claims the passage has no other Tajwid rule. Zero results are not a claim of
  absence.
- `total`, `offset`, `next_offset` page the annotations (`limit` 1 to 500, default 100);
  `rule_counts` count every occurrence, not only the returned window.
- `unresolved` counts positions needing missing context; `skipped` counts positions a
  detector deliberately left out (for example lafz al-jalala, letter-name noon).
- The Tajwid tools read the bundled Quran snapshot (or `WIRDI_AI_ROOT` when set) for Quran text and the knowledge store for rules.
  A missing or altered store gives `DATA_UNAVAILABLE` or `INTEGRITY_FAILURE` for that tool
  only; other tools keep answering. Errors never contain a path or book text.

## Source-page tools

Books are not distributed and their licence is unknown, so pages exist only where a user built
them locally (git-ignored) with `scripts/build_page_store.py`. The store is verified by hash on
every read. `text_quality` states that extraction is raw (book A has inverted lam-alef
ligatures). `search_source_pages` folds marks, letter variants and that inversion, so its
`snippet` is a normalized search form, not source text. Copy-protected PDFs are never
extracted.

## Shared response contract

```text
Success[T] = {
  schema_version: "1.0", status: "ok", data: T,
  provenance: [...], validation_status: "...", warnings: [...]
}
Failure = {
  schema_version: "1.0", status: "error",
  error: { code: "...", message: "...", retryable: false }
}
```

Typed error codes used by these tools: `INVALID_REFERENCE`, `NOT_FOUND`,
`UNSUPPORTED_VERSION`, `DATA_UNAVAILABLE`, `INTEGRITY_FAILURE`, `UNSUPPORTED_CAPABILITY`.
Real stdio tests (`tests/integration/test_tajwid_stdio.py`) exercise every tool, the
isolation cases and the error semantics.

## `list_reading_combinations`

Each madd occurrence lists its own `variants`. The longer book (Nabhan pp.98-108, « ترتيب الأوجه » and
« تسوية المدود ») says which choices may be taken together in one ayah. The tool returns, for each ayah of
the selection that holds a madd or a plural meem, its `positions` (rule, kind, anchor and, for a madd made
'arid by the stop, the vowel of the hamza) and the legal `combinations`, one reading per position, in the
book's order (iskan before sila, short before long).

| `basis` | Meaning |
| --- | --- |
| `single_position` | One madd: its own readings, nothing to combine |
| `book_listed` | Exactly two positions and the book tabulates the pair: the list is the book's (for example 7 readings for a separated madd then a connected madd made 'arid with a fatha) |
| `pairwise_extension` | Three or more positions: every pair obeys the book's table. This extends the book's equalising rule and is an inference |
| `unconstrained` | The book gives no table for these kinds together, so the readings are free |

`max_combinations` (1 to 500, default 200) truncates a long list and sets `truncated`; `total` is always
the full count. A reading is `4_harakat`, `3_harakat+rawm`, `sila_2_harakat`, `iskan`… Nothing is chosen
and every reading comes from an unreviewed source.

