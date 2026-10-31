# Handoff

Branch `feat/tajwid-knowledge` (never pushed). Version 0.6.0. Read
[PROGRESS](PROGRESS.md) for the commit-by-commit state and [DECISIONS](DECISIONS.md) for
what was decided without you.

## What works (verified end to end)

- Twelve tools over a real stdio MCP client: [E2E_REPORT](E2E_REPORT.md) is the
  transcript (0 unexpected outcomes); `tests/integration/test_tajwid_stdio.py` runs the same
  tools plus the isolation cases (missing Quran root, missing knowledge store, a rule file
  altered by one byte, an oversized page range, invalid parameters).
- Latency ([PERF](PERF.md)): cold start 0.57 s; one 559-layout page 106 ms p50; 50 ayat 125 ms.
- All 6,214 single-ayah selections in both reading modes and all 559 application pages run
  without an exception; counts per rule are in [RULE_AUDIT](RULE_AUDIT.md); no rule is at
  zero or abnormally high.
- The corpus checksum drift was resolved by a controlled manifest update after the full
  mapping conformance passed ([SOURCE_AUDIT](SOURCE_AUDIT.md)); mapping works again.
- Offline suite: 140+ tests; with `WIRDI_TEST_SOURCE_ROOT` the full suite (170) passes.
- **0.6.0 adds Book A** (every section of its 51 pages): 67 more rule records and 65 more
  detectors for madd, hamza, heavy and light letters, taqlil, general idgham and ya'at al-idafa,
  and the `get_letter_properties` tool. [BOOK_A_COVERAGE](BOOK_A_COVERAGE.md) says rule by rule
  what is detected and what is not; [TESTING_GUIDE](TESTING_GUIDE.md) has a request for each family.
  **Correction to the previous handoff:** madd, hamza, ra, imala and ya'at are in Book A, not only
  in Book B.

## What is partial

- **Everything Tajwid is unreviewed.** 14 rules, each citing book A and, for 12 of them, book B
  (Abu Nashit) by page. No annotation can be `scholarly_verified`; the highest served status is
  `candidate`. `get_tajwid_explanation` always returns `UNSUPPORTED_CAPABILITY`.
- **Coverage per rule** (candidates in the corpus, waqf reading; cited pages):

| Rule | Candidates | Cited pages |
| --- | ---: | --- |
| `qalqala_sughra` | 2,933 | A p.44; B pp.52-53 |
| `qalqala_kubra` | 912 | A p.44; B pp.52-53 |
| `idhar_halqi` | 3,009 | A pp.4-5; B pp.56-57 |
| `idgham_bighunna` | 3,923 | A pp.5-6; B pp.57-58 |
| `idgham_bilaghunna` | 1,039 | A p.5; B pp.57-58 |
| `iqlab` | 283 | A p.7; B p.59 |
| `ikhfa_haqiqi` | 5,307 | A pp.7-8; B p.60 |
| `idhar_mutlaq` | 125 | A p.6; B p.58 |
| `ikhfa_shafawi` | 496 | A p.9; B p.62 |
| `idgham_shafawi` | 832 | A p.9; B p.62 |
| `idhar_shafawi` | 6,155 | A pp.9-10; B p.63 |
| `ghunna_mushaddad` | 7,336 | A p.11; B p.63 |
| `lam_shamsiya` | 4,042 | A pp.12-13 only |
| `lam_qamariya` | 5,370 | A p.13 only |

- **Not covered:** the Book A items marked "not covered" or "record only" in
  [BOOK_A_COVERAGE](BOOK_A_COVERAGE.md) (two hamzas in two words, the vowel of other sakin letters
  before hamzat al-wasl, the default closed ya, joining a wasl and a qat' hamza in a word), waqf and
  ibtida rules, waqf signs inside an ayah, and the Book B sections that were not drafted.
- **In `wasl` mode** a single ayah cannot decide its last word-final noon, tanween or mim; they are
  reported under `unresolved` (pass `following`).
- **Book B was read only as page images** (it is a copy-protected scan; protection was not
  bypassed and there is no OCR). Its citations come from reading pages 52-54, 56-63 and the
  contents pages by eye; the other pages cited are the contents page numbers. Treat the B
  citations as needing a second pair of eyes. The author name on its cover is a reading to confirm.
- **Book A text is raw:** the local page store (built on this machine, git-ignored) has inverted
  lam-alef ligatures; search tolerates them but the text is not clean.
- **Rule records are paraphrases drafted by the assistant.** They must be proofread against the
  books before anyone relies on them.
- **Source divergence recorded, not resolved:** books A (pp.5-6) and B (p.58) classify the
  completeness of the idgham with ghunna differently.

## Pages and items to review first

1. The 81 records in `knowledge/rules/` against the cited pages (the 14 first records: A pp.4-13
   and 44, B pp.52-53, 56-60, 62-63; the 67 Book A records: the pages in each citation, which
   are where the section begins).
2. [REVIEW_SAMPLE](REVIEW_SAMPLE.md): five candidates per rule, references only.
3. The 49 alef-lam words skipped as not fitting the article pattern (audit, "skipped"), and the
   `lam_*` rules which cite book A alone.
4. The coloured mushaf is **not** used. If you want it later, see [PILOT_REPORT](PILOT_REPORT.md).

## Decisions taken in your place

See [DECISIONS](DECISIONS.md): no reviewer so nothing above `candidate`; Abu Nashit is a
documented hypothesis with `tariq=unspecified` kept for the corpus; waqf as the mushaf default
(unused, since the extraction was a NO-GO); the manifest drift admitted after conformance;
mushaf NO-GO; rule tariq assignment; candidates returned by default; the two books' disagreement
not arbitrated.

## Questions for you

1. **Who is the qualified reviewer** (name, qualification)? Without one the work stops at
   `candidate`; the validation store is ready and empty.
2. **Licence:** books A and B and the mushaf are of unknown licence. May the paraphrased rule
   records, which cite them by page, stay in the repository? May a local page store be shared?
3. **Abu Nashit:** may the corpus be treated as Abu Nashit for these rules, or must it stay
   `unspecified` until a source attests it for `qalun.json`?
4. **Display in version 1:** should the application show unreviewed candidates (labelled) or
   nothing until a reviewer approves?
5. **Integration into wirdi-Ai** was not started (out of scope); the contract is in
   [INTEGRATION](INTEGRATION.md). Do you want it next, behind the "verified only" rule?
6. Book A is now covered. Should the Abu Nashit differences of Book B be drafted next, or should
   the reviewer be found first? (Book B has not been used for the 65 new records.)

## Reproduce

```bash
.venv/bin/python -m pytest -q                       # offline
WIRDI_TEST_SOURCE_ROOT=/home/najjar/Documents/Me/wirdi-Ai .venv/bin/python -m pytest -q
.venv/bin/ruff check . && .venv/bin/ruff format --check .
.venv/bin/python scripts/build_rule_manifest.py --check
.venv/bin/python scripts/audit_rules.py --source-root /home/najjar/Documents/Me/wirdi-Ai
.venv/bin/python scripts/e2e_report.py --source-root /home/najjar/Documents/Me/wirdi-Ai
git ls-files | grep -i -E '\.(pdf|png|jpe?g)$'      # must print nothing
```

The PDFs stay in `docs/` (git-ignored). An installed wheel does not contain `knowledge/`:
point `WIRDI_KNOWLEDGE_ROOT` at it, or run from the checkout.
