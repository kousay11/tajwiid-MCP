# Wirdi MCP

A local, read-only MCP server for **Qaloun (from Nafi')**: it serves the unchanged Qaloun text of
the Wirdi AI corpus and proposes **candidate** Tajwid annotations, each tied to the exact letters,
the reading context and the page of the book that states the rule. Everything is deterministic:
there is no LLM, no embedding, no RAG, no database and no network access.

**Version 0.6.0.** 12 tools over stdio, 81 rule records (14 + 67 from Book A), 79 detectors.
**Nothing is scholarly verified**: no qualified reviewer has been named, so the highest status the
server ever returns is `candidate`.

> **Résumé en français.** Serveur MCP local (stdio) pour la riwaya de Qaloun d'après Nafi'. Il lit
> le texte Qaloun du dépôt Wirdi AI (sans le modifier) et propose des annotations de tajwid
> *candidates* (madd, hamza, tafkhim/tarqiq, idgham, ياءات الإضافة, noon/mim sakina, qalqala…), avec
> la lettre exacte, le contexte (waqf/wasl), la page de l'application et la page du livre cité.
> Aucune annotation n'est validée par un savant : le statut maximal est `candidate`.
> Pour tester : [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md) ; pour les pièges rencontrés :
> [docs/NoteImportant.md](docs/NoteImportant.md).

## What it is, and what it is not

| It is | It is not |
| --- | --- |
| A deterministic source of *candidate* annotations, each with its evidence and its page | A statement that a recitation is correct |
| Read-only: the Quran text is never modified or copied | A Quran database, an importer or a search engine over the Quran |
| Explicit about what it cannot decide (`unresolved`, `skipped`, `variants`, `limitations`) | A chooser between readings the books allow: `variants` lists them all |
| Local: stdio only, no network listener | An integration into the Wirdi AI application (not started) |

Rules the project keeps: the Quran text is immutable; no Hafs rule is assumed for Qaloun; a status
above `candidate` needs a named reviewer; divergent sources are shown, never silently arbitrated;
no PDF, page image or book text is committed.

## Quick start

Requires Python 3.12+.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
export WIRDI_AI_ROOT=/absolute/path/to/wirdi-Ai
.venv/bin/wirdi-mcp          # waits for MCP input on stdin
```

| Variable | Purpose |
| --- | --- |
| `WIRDI_AI_ROOT` | Root of the Wirdi AI checkout. Its public files are the only source of Quran text. Without it every tool that reads the Quran returns `DATA_UNAVAILABLE` and `health_check` shows `quran_data: not_configured` |
| `WIRDI_KNOWLEDGE_ROOT` | Alternative `knowledge/` directory (default: the one in this repository) |
| `WIRDI_MCP_LOG_LEVEL` | Log level, written to stderr |
| `WIRDI_TEST_SOURCE_ROOT` | Tests only: enables the read-only real-corpus tests |

`.env` is not loaded automatically. An installed wheel does not contain `knowledge/`: point
`WIRDI_KNOWLEDGE_ROOT` at it, or run from the checkout.

**MCP host configuration**

```json
{
  "mcpServers": {
    "wirdi": {
      "command": "/absolute/path/wirdi-mcp/.venv/bin/wirdi-mcp",
      "env": {"WIRDI_AI_ROOT": "/absolute/path/wirdi-Ai", "WIRDI_MCP_LOG_LEVEL": "INFO"}
    }
  }
}
```

**MCP Inspector.** The Inspector starts the server with a filtered environment, so a variable
written before `npx` does not reach it. Pass it with `-e`, or in the « Environment Variables » field
of the interface, then reconnect:

```bash
npx @modelcontextprotocol/inspector -e WIRDI_AI_ROOT=/absolute/path/wirdi-Ai .venv/bin/wirdi-mcp
```

Check with `health_check`: `quran_data` must be `configured_unchecked`.

## The 12 tools

All tools are read-only and return `{status: "ok", data, provenance, validation_status, warnings}`
or `{status: "error", error: {code, message, retryable}}`.

| Tool | Arguments | Returns |
| --- | --- | --- |
| `health_check` | none | Readiness and configuration; reads no data |
| `get_qaloun_passage` | `selection` | The unchanged ayat with their SHA-256 and the 559-page span |
| `resolve_source_mapping` | `selection`, `target_corpus_id`, `target_corpus_version`, `target_numbering_system` | Mapping of the selection to another numbering (e.g. Hafs/Kufian), with `mapping_status` and `safe_for_source_retrieval` |
| `list_tajwid_rules` | `family?` | The 81 rules: id, Arabic name, family, detectability, tariq, `has_detector` |
| `get_tajwid_rule` | `rule_id`, `version` | One rule record: definition, conditions, exceptions, limitations, book and page citations |
| `analyze_qaloun_tajwid` | `selection` (1 to 100 ayat), `reading_context`, `rule_ids?`, `families?`, `limit` (≤500), `offset` | Candidate annotations, paged, with counts, `unresolved`, `skipped`, `coverage` |
| `summarize_tajwid` | `surah`, `start_ayah?`, `end_ayah?`, `reading_context`, `rule_ids?`, `families?`, `limit`, `offset` | Counts per rule and per ayah (≤300 ayat) |
| `analyze_app_page` | `page` (1 to 559), `reading_context`, `rule_ids?`, `families?`, `limit`, `offset` | Candidates for the ayat that begin on that page of the verified 559-page layout |
| `get_letter_properties` | `letters` (1 to 29 base letters) | Place of articulation and characteristics (Book A pp.40-45) |
| `get_source_page` | `edition_id`, `page_start`, `page_end` (≤5 pages) | Raw page text from the local, git-ignored page store |
| `search_source_pages` | `query` (2 to 80 chars), `edition_ids`, `limit` | Pages containing the word, with a normalised search snippet |
| `get_tajwid_explanation` | `annotation_id`, `annotation_version`, `language` | **Always** `UNSUPPORTED_CAPABILITY` until a named reviewer validates annotations |

**Error codes**: `INVALID_REFERENCE`, `NOT_FOUND`, `UNSUPPORTED_VERSION`, `DATA_UNAVAILABLE`,
`INTEGRITY_FAILURE`, `UNSUPPORTED_CAPABILITY`. A missing or altered store fails that tool only, and
typed; errors never contain a path or book text.

### Selections and the reading context

A selection is `{"start": <reference>, "end_ayah": N}`. A reference carries the corpus identity:

```json
{"corpus_id": "wirdi-ai:quranpedia:qalun", "corpus_version": "sha256:ece0a2b0…d1303",
 "numbering_system": "wirdi-ai:qalun-6214", "riwaya": "qaloun", "tariq": "unspecified",
 "surah": 2, "ayah": 5}
```

`reading_context.mode` decides what a word-final letter does:

- **`waqf`**: the reading stops at the end of **each selected ayah, and nowhere else**. Inside an
  ayah the reading is continuous, so a mim in the middle of an ayah is still read with the next
  word. Waqf signs inside an ayah are not treated as stops. To simulate a stop on a word, pass
  `stop_after_word`.
- **`wasl`**: continuous reading across the selection. The last position of the last ayah needs the
  following ayah: pass `following` (a full reference to the next ayah of the same surah) or the
  position is reported under `unresolved`.

Waqf-only rules (`madd_arid_sukun`, `madd_lin`, `madd_iwad`, `madd_muttasil_arid`,
`ra_mutatarrif_*`) never fire in `wasl`. `following` must be `null` or a complete reference.

## What an annotation says

```
rule_id, rule_version        which rule, and its version
anchor                       ayah SHA-256 + codepoint range into the unchanged text + word index
reading_context              waqf or wasl, and what was assumed
status                       always "candidate"
evidence                     book, edition and page of the rule (never a verdict)
page_refs                    the 559-page application span of the ayah
note                         what the detector saw, in words
variants                     the readings the book allows here; the engine never picks one
```

An empty or short result is **not** a claim that a passage has no other rule: only the listed
rules are evaluated, and `coverage` says whether every requested position could be decided.

## Rules

81 paraphrased, page-cited records in `knowledge/rules/`, all `unreviewed`. The text of a record is
a short paraphrase written for this project, never a quotation.

| Family | Rules | Examples |
| --- | ---: | --- |
| `madd` | 23 | natural, badal, 'iwad, muttasil, munfasil, 'arid, lin, lazim (kalimi/harfi), sila of the ha and of the meem, fixed alefs, alef of ana |
| `hamza` | 19 | replaced hamzas, the prophet words, two hamzas in a word, repeated interrogatives, hamzat al-wasl, vowel of a sakin before it |
| `tafkhim_tarqiq` | 12 | ra, the lam of Allah, the alef, the ghunna |
| `ya_idafa` | 6 | open and closed first-person ya, `معي`, `ربي` of Fussilat |
| `idgham_general` | 5 | mutamathilayn, mutajanisayn, mutaqaribayn, naqis, the great idgham of تأمنا |
| `noon_sakina_tanween` | 6 | idhar halqi/mutlaq, idgham with/without ghunna, iqlab, ikhfa |
| `mim_sakina` | 3 | ikhfa, idgham, idhar shafawi |
| `imala_taqlil`, `lam_taarif`, `qalqala` | 2 each | taqlil of التوراة, imala of هار; article lam; qalqala sughra/kubra |
| `ghunna` | 1 | geminated noon and meem |

Each record has a **detectability**: `A` mechanical, `B` depends on the stop or the neighbouring
word, `C` a closed word list named by the book. Two records (`hamza_two_words_same`,
`hamza_two_words_different`) have no detector: the Qaloun text already carries the result of the
rule, not the original hamzas.

**Tariq.** The corpus identifies Qaloun but does not attest Abu Nashit, so its tariq is
`unspecified`. The 12 first-release rules that cite Book B (the Abu Nashit source) carry
`abu_nashit`; the 69 others, which rest on Book A alone, carry `unspecified`.

### What the corpus spelling tells the detectors

The detectors read signs the corpus writes, not assumptions: a maddah marks the long madds; a
superscript alef marks a madd alef; the small waw or yeh on a ha marks the sila; a sakin noon or
meem before idgham, ikhfa and iqlab letters has no sukun; an alef inserted between two hamzas is a
superscript alef; the open first-person ya is spelled with a fatha and the closed one with the yeh
barree; hamzat al-wasl has three different marks. Where a rule needs a word list, the list is the
book's own, matched on a normalised skeleton and on the **Kufian** ayah number the book uses.

## Data and numbering

| Datum | Origin | Guard |
| --- | --- | --- |
| Quran text | The public files of the Wirdi AI checkout: KFGQPC Qaloun via Qur'anpedia (`risan/quran-json`, commit `6523a9ad…`), 6,214 ayat | SHA-256 of the corpus checked on every call; text never modified or copied |
| 559-page layout | Same checkout | SHA-256 checked; `verified_against_edition` |
| Rules | `knowledge/rules/*/1.json` | `manifest.json` pins every file; one altered byte gives `INTEGRITY_FAILURE` |
| Books | Local PDFs in `docs/` | Never committed; only paraphrased rules with a page citation are |

**Two numberings meet here.** The corpus, the tools and the application use the **Qaloun count**
(6,214 ayat, `wirdi-ai:qalun-6214`). The Tunisian Hannibal mushaf and the place numbers of Book A
use the **Kufian count** (6,236 ayat), kept in the corpus as `number_in_hafs`. 78 Qaloun ayat
gather two Kufian numbers and 59 Kufian ayat are split, touching 59 surahs: in Al-Baqara, Qaloun
2:5 is Kufian 2:6 and Qaloun 2:7 is 2:8. Use `resolve_source_mapping` to convert. The application
layout has **559** pages and the Hannibal mushaf 604: pages are never compared by number, only
through the verse.

## Sources and their limits

| Source | Role | State |
| --- | --- | --- |
| **Book A**, *أحكام رواية قالون عن نافع المدني* (51 pp., text layer) | Base of the 67 new rules; Qaloun, does not name Abu Nashit | Read on page images for the citations; inconsistent in places (below) |
| **Book B**, *مذكرة في أحكام الترتيل… من طريق أبي نشيط* (156 pp.) | Cited by 12 first-release rules | A copy-protected scan: protection is never bypassed, there is no OCR; cited from page images only |
| **Hannibal mushaf** (Tunis, coloured) | Evaluated for extracting the colours | **NO-GO** ([PILOT_REPORT](docs/PILOT_REPORT.md)); not used |

All three have an unknown licence. Book A's text layer is raw (inverted lam-alef ligatures).

**Where Book A contradicts itself** (each case is recorded in the rule limits and in
[BOOK_A_COVERAGE](docs/BOOK_A_COVERAGE.md); none is arbitrated): `فألقه` (p.19 against p.20) and
`يأته` carry `variants`; `آلآن` has three readings; four place numbers of the ya'at lists differ
between p.46 and p.49; the sentence on `معي` (p.47) is the reverse of the corpus spelling and of the
book's own classes. The 1,314 plural meems written bare before ba and meem take the sila by the
general wording of p.17; their interaction with ikhfa/idgham shafawi is an **inference**, written in
both annotations. A reviewer has also questioned the madd lengths (2 or 4, and 4) that Book A gives
as 2, 3 or 4, and 3 or 4: the divergence is open.

## Not covered

Waqf and ibtida rules; the alef after a non-inclined ra (p.35); two hamzas in two words; the default
closed ya before an ordinary letter beyond the seven named examples; joining a wasl and a qat' hamza
in one word; the vowel of sakin letters before hamzat al-wasl beyond `من`, the plural meem and
tanween; the Book B sections not drafted; and everything Book A itself does not say (it is a
51-page summary). [BOOK_A_COVERAGE](docs/BOOK_A_COVERAGE.md) lists each section and its state.

## Tests and verification

```bash
.venv/bin/python -m pytest                                          # offline: 166 tests
WIRDI_TEST_SOURCE_ROOT=/abs/wirdi-Ai .venv/bin/python -m pytest    # + real corpus: 197 tests
.venv/bin/ruff check . && .venv/bin/ruff format --check .
.venv/bin/python scripts/build_rule_manifest.py --check
```

- The offline suite uses synthetic orthographic fixtures modelled on the books' examples, and real
  stdio subprocess tests. The real-corpus suite runs every single-ayah selection in both modes,
  every one of the 559 pages, the closed word lists (each must hit exactly the places the book
  names) and the corpus lookups behind the page contradictions.
- [TESTING_GUIDE](docs/TESTING_GUIDE.md) gives a request for every rule family; run them in the
  Inspector and compare with [NoteImportant](docs/NoteImportant.md), which records the tests already
  done and their analysis.
- Measured latency ([PERF](docs/PERF.md)): cold start 0.57 s; one application page about 106 ms (p50).

## Repository layout

```
src/wirdi_mcp/
  server.py, config.py        entry point and configuration
  domain/                     typed contracts (Pydantic): annotations, statuses, references
  quran/                      checksum-pinned, read-only access to the Wirdi AI files
  mapping/                    the existing mapping authority (Qaloun <-> Hafs)
  knowledge/                  rule registry (hash-pinned), page store (local, fail-closed)
  tajwid/                     tokenizer and detectors: madd, hamza, tafkhim, idgham, yaat,
                              lexicon (word lists), letters (static tables), engine, service
  tools/                      the 12 MCP tools and their contracts
knowledge/rules/              81 rule records + manifest.json     (committed)
knowledge/sources/            edition metadata only               (no book text)
knowledge/validation/         empty, ready for a reviewer's records
scripts/                      rule generation, manifest, audit, E2E report, perf, page store
tests/                        unit and integration tests
docs/                         design, audits, reports and guides (PDFs here are git-ignored)
```

| Script | Use |
| --- | --- |
| `build_book_a_rules.py` | Writes the 67 Book A rule records from one table; then run `build_rule_manifest.py` |
| `build_rule_manifest.py [--check]` | Validates every record and writes or checks the manifest |
| `audit_rules.py --source-root …` | Counts every rule over all 6,214 ayat in both modes, flags zero or abnormal ones |
| `e2e_report.py --source-root … --out …` | Real stdio transcript of every tool, with no Quran or book text |
| `measure_perf.py --source-root …` | Cold start and per-call latency |
| `build_page_store.py <pdf> <edition>` | Builds the local page store for a PDF with a text layer (refuses protected PDFs) |
| `verify_local.py --source-root …` | Short real-stdio verification |

## What needs a human

1. **A named, qualified reviewer.** Without one nothing moves beyond `candidate`; the validation
   store is ready and empty.
2. **Licences** of the books and the mushaf, and whether the paraphrased records may stay in the
   repository.
3. **The Abu Nashit question**: may the corpus be treated as Abu Nashit for these rules?
4. **Display in version 1** of the application: label unreviewed candidates, or show nothing until
   a reviewer approves?
5. **Arbitration** of the divergences listed above, with the reviewer.
6. **Integration into Wirdi AI** (not started): see [INTEGRATION](docs/INTEGRATION.md).

## Documentation

| Document | Contents |
| --- | --- |
| [NoteImportant](docs/NoteImportant.md) | Inspector setup, data origin, results already tested and their analysis |
| [TESTING_GUIDE](docs/TESTING_GUIDE.md) | A request per rule family and what to check |
| [BOOK_A_COVERAGE](docs/BOOK_A_COVERAGE.md) | Each Book A section, its rules, its state and the page contradictions |
| [MCP_TOOLS](docs/MCP_TOOLS.md) | Tool contracts, statuses, reading context and failure semantics |
| [TAJWID_ENGINE](docs/TAJWID_ENGINE.md) | Rule, detector, annotation, review and explanation, kept separate |
| [RULE_AUDIT](docs/RULE_AUDIT.md) | Per-rule counts over the whole corpus |
| [ARCHITECTURE](docs/ARCHITECTURE.md), [SOURCE_AUDIT](docs/SOURCE_AUDIT.md) | Boundaries, reference identity, the corpus and its checksums |
| [PERF](docs/PERF.md), [E2E_REPORT](docs/E2E_REPORT.md) | Measured latency; a real stdio transcript |
| [SOURCES_INTAKE](docs/SOURCES_INTAKE.md), [PILOT_REPORT](docs/PILOT_REPORT.md) | The three source PDFs; the coloured-mushaf pilot (NO-GO) |
| [DECISIONS](docs/DECISIONS.md), [BLOCKERS](docs/BLOCKERS.md), [PROGRESS](docs/PROGRESS.md), [HANDOFF](docs/HANDOFF.md), [ROADMAP](docs/ROADMAP.md) | Decisions taken, blockers, where the work stands |
| [INTEGRATION](docs/INTEGRATION.md) | The planned client contract for Wirdi AI |

The official [`mcp` Python SDK](https://github.com/modelcontextprotocol/python-sdk) is pinned to
2.3.0; this project uses its `MCPServer` API, not the separate `fastmcp` package.
