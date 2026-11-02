# Wirdi MCP

A **local MCP server for the Qaloun recitation (from Nafi')**. You give it a passage of the Quran;
it gives you back the **Tajwid rules that apply to it**, letter by letter, each with the page of
the book that states the rule.

- **Version 0.6.0** · 12 tools · 97 rules · 97 detectors · 322 tests (289 on a clean clone, the rest also check the original Wirdi AI files)
- **Read-only and deterministic**: no LLM, no RAG, no database, no network. The Quran text is read
  from the Wirdi AI files and never modified.
- **Nothing is scholarly verified.** No qualified reviewer has been named, so every result is a
  `candidate`. The server never says more than that.

> **En français.** Serveur MCP local (stdio) pour Qaloun d'après Nafi'. Vous donnez un passage ; il
> renvoie les règles de tajwid applicables (madd, hamza, tafkhim/tarqiq, idgham, ياءات الإضافة,
> noon/mim sakina, qalqala…), avec la lettre exacte, le contexte (waqf/wasl) et la page du livre
> cité. Aucune annotation n'est validée par un savant : le statut maximal est `candidate`.
> Requêtes prêtes à coller : [docs/APPLY.json](docs/APPLY.json). Pièges déjà rencontrés :
> [docs/NoteImportant.md](docs/NoteImportant.md).

## Contents

1. [How it works](#1-how-it-works)
2. [Quick start](#2-quick-start)
3. [Key commands](#3-key-commands)
4. [The 12 tools](#4-the-12-tools)
5. [Selections and reading context](#5-selections-and-reading-context)
6. [What an annotation says](#6-what-an-annotation-says)
7. [All 97 rules](#7-all-97-rules)
8. [Data and numbering](#8-data-and-numbering)
9. [Sources and where they disagree](#9-sources-and-where-they-disagree)
10. [What is not covered](#10-what-is-not-covered)
11. [Tests](#11-tests)
12. [Repository layout and scripts](#12-repository-layout-and-scripts)
13. [What needs a human](#13-what-needs-a-human)
14. [Documentation index](#14-documentation-index)

---

## 1. How it works

```
 your request                                      the answer
 ───────────                                       ──────────
 selection (surah, ayah range)        ┌─────────►  annotations: rule, exact letters,
 + reading context (waqf / wasl)      │            note, variants, page, book citation
 + optional filter (family, rules)    │            + counts, unresolved, skipped, coverage
        │                             │
        ▼                             │
 1. check   the corpus SHA-256 matches the pinned one (fail closed)
 2. read    the unchanged ayat of the Qaloun corpus
 3. split   each ayah into words and letters, with reversible codepoint offsets
 4. detect  one deterministic detector per rule family reads the letters and their signs
 5. attach  rule record (hash-checked) → citation, page; the ayah's 559-page span
 6. report  what could not be decided: `unresolved` (missing context), `skipped` (out of scope)
```

Four ideas hold the design together:

| Idea | What it means in practice |
| --- | --- |
| **A candidate is not a verdict** | Every annotation is `candidate`. Nothing is promoted without a named reviewer |
| **The text decides, not an assumption** | Detectors read the signs the corpus writes (maddah, small waw/yeh, sukun, shadda…); no Hafs rule is assumed |
| **Several readings are listed, never chosen** | Where a book allows 2, 3 or 4 harakat, `variants` shows all of them |
| **Missing context is said, not guessed** | A word-final letter at the end of a `wasl` selection is `unresolved` until you give the next ayah |

## 2. Quick start

Requires Python 3.12+.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/wirdi-mcp          # waits for MCP input on stdin; no network listener
```

| Variable | Purpose |
| --- | --- |
| *(none needed)* | The Quran text, the 559-page map and the mapping resolver are **bundled** in the package (`src/wirdi_mcp/quran/snapshot/`, SHA-256 pinned). A clean clone calls every tool |
| `WIRDI_AI_ROOT` | Optional. Path of a Wirdi AI checkout: the server then reads and verifies the original files instead of the snapshot |
| `WIRDI_QURAN_SOURCE` | Optional. `none` disables the Quran source: tools that read it return `DATA_UNAVAILABLE` and `health_check` shows `quran_data: not_configured` |
| `WIRDI_KNOWLEDGE_ROOT` | Another `knowledge/` directory (default: this repository's) |
| `WIRDI_MCP_LOG_LEVEL` | Log level, written to stderr |
| `WIRDI_TEST_SOURCE_ROOT` | Tests only: enables the real-corpus tests |

**Use it from an MCP client** (replace the paths):

```json
{
  "mcpServers": {
    "wirdi": {
      "command": "/absolute/path/wirdi-mcp/.venv/bin/wirdi-mcp",
      "env": {"WIRDI_MCP_LOG_LEVEL": "INFO"}
    }
  }
}
```

**Try it in the MCP Inspector.**

```bash
npx @modelcontextprotocol/inspector .venv/bin/wirdi-mcp
```

Then call `health_check`: `quran_data` must be `configured_unchecked` and `quran_source` `bundled`.
(The Inspector starts the server with a *filtered* environment: to set `WIRDI_AI_ROOT`, pass it with
`-e WIRDI_AI_ROOT=/path`, not as a variable written before `npx`.) **Ready-to-paste requests for
every tool are in [docs/APPLY.json](docs/APPLY.json).**

## 3. Key commands

| I want to… | Command |
| --- | --- |
| Start the server | `.venv/bin/wirdi-mcp` |
| Check it works end to end | `.venv/bin/python scripts/verify_local.py` |
| Run the tests (bundled snapshot, real corpus included) | `.venv/bin/python -m pytest` |
| Also check against a Wirdi AI checkout | `WIRDI_TEST_SOURCE_ROOT=/abs/wirdi-Ai .venv/bin/python -m pytest` |
| Lint and format | `.venv/bin/ruff check . && .venv/bin/ruff format --check .` |
| Change a rule record | edit the table in `scripts/build_book_a_rules.py`, then `python scripts/build_book_a_rules.py && python scripts/build_rule_manifest.py` |
| Check the rule files against the manifest | `.venv/bin/python scripts/build_rule_manifest.py --check` |
| Count every rule over the 6,214 ayat | `.venv/bin/python scripts/audit_rules.py --source-root /abs/wirdi-Ai` |
| One correct JSON request per tool, run against the server | `docs/EXEMPLES_REQUETES.md` (rebuild: `.venv/bin/python scripts/build_examples_md.py`) |
| Build the local page store of a book | `.venv/bin/python scripts/build_page_store.py <pdf> <edition-id>` |

**After changing a rule or a detector**, in this order: regenerate the records and the manifest →
run both test suites → regenerate the audit (`RULE_AUDIT.md`).

## 4. The 12 tools

Every tool is read-only. A success is `{status: "ok", data, provenance, validation_status,
warnings}`; a failure is `{status: "error", error: {code, message, retryable}}`.

| Tool | You give | You get |
| --- | --- | --- |
| `health_check` | nothing | Readiness and configuration; reads no data |
| `get_qaloun_passage` | `selection` | The unchanged ayat, their SHA-256 and their 559-page span |
| `resolve_source_mapping` | `selection`, `target_corpus_id`, `target_corpus_version`, `target_numbering_system` | Where the selection falls in another numbering (e.g. Kufian/Hafs), `mapping_status`, `safe_for_source_retrieval` |
| `list_tajwid_rules` | `family?` | The 97 rules: id, Arabic name, family, type, `has_detector` |
| `get_tajwid_rule` | `rule_id`, `version` | One rule record: definition, conditions, exceptions, limits, book and page |
| `analyze_qaloun_tajwid` | `selection` (1 to 100 ayat), `reading_context`, `rule_ids?`, `families?`, `limit` (≤500), `offset` | Candidate annotations, paged, with counts, `unresolved`, `skipped`, `coverage` |
| `summarize_tajwid` | `surah`, `start_ayah?`, `end_ayah?`, `reading_context`, `rule_ids?`, `families?`, `limit`, `offset` | Counts per rule and per ayah (≤300 ayat) |
| `analyze_app_page` | `page` (1 to 559), `reading_context`, `rule_ids?`, `families?`, `limit`, `offset` | Candidates for the ayat that begin on that page of the application layout |
| `list_reading_combinations` | `selection`, `reading_context`, `max_combinations` (≤500) | For each ayah with a madd or a plural meem, the readings that may be taken together, from the book's own tables (Nabhan pp.98-108); `basis` says whether the book lists the pair, extends it, or gives no table |
| `get_letter_properties` | `letters` (1 to 29 base letters) | Place of articulation and characteristics (Book A pp.40-45) |
| `get_source_page` | `edition_id`, `page_start`, `page_end` (≤5) | Raw text of pages from the local page store |
| `search_source_pages` | `query` (2 to 80 characters), `edition_ids`, `limit` | The pages that contain the word, with a normalised snippet |

**Error codes:** `INVALID_REFERENCE`, `NOT_FOUND`, `UNSUPPORTED_VERSION`, `DATA_UNAVAILABLE`,
`INTEGRITY_FAILURE`, `UNSUPPORTED_CAPABILITY`. A missing or altered store fails that one tool, typed;
an error never contains a path or book text.

## 5. Selections and reading context

A **selection** is `{"start": <reference>, "end_ayah": N}`. A **reference** names the corpus:

```json
{"corpus_id": "wirdi-ai:quranpedia:qalun",
 "corpus_version": "sha256:ece0a2b0efe44d496211c595d0a34f495413bc93f78fba8095a666e2048d1303",
 "numbering_system": "wirdi-ai:qalun-6214", "riwaya": "qaloun", "tariq": "unspecified",
 "surah": 2, "ayah": 5}
```

The **reading context** decides what a word-final letter does:

| Field | Meaning |
| --- | --- |
| `mode: "waqf"` | The reading stops at the end of **each selected ayah, and nowhere else**. Inside an ayah the reading is continuous: a mim in the middle of an ayah is still read with the next word |
| `mode: "wasl"` | Continuous reading across the whole selection. The last position of the last ayah needs the next ayah, otherwise it is reported under `unresolved` |
| `following` | A complete reference to the next ayah of the same surah (for `wasl`), or `null` |
| `stop_after_word` | Stop the last ayah after that many words, to simulate a stop inside an ayah |

Waqf-only rules (`madd_arid_sukun`, `madd_lin`, `madd_iwad`, `madd_muttasil_arid`, `ra_mutatarrif_*`)
never fire in `wasl`. Waqf signs written inside an ayah are not treated as stops.

## 6. What an annotation says

| Field | Content |
| --- | --- |
| `rule_id`, `rule_version` | Which rule |
| `anchor` | The ayah's SHA-256, the codepoint range into the unchanged text, the word index |
| `reading_context` | Waqf or wasl, and what was assumed |
| `status` | Always `candidate` |
| `evidence` | Book, edition and page of the rule (a source, never a verdict) |
| `page_refs` | The 559-page application span of the ayah |
| `note` | What the detector saw, in words |
| `variants` | The readings the book allows here; the engine never picks one |

A short or empty result is **not** a claim that the passage has no other rule: only the rules you
ask for are evaluated, and `coverage` says whether every position could be decided.

## 7. All 97 rules

Each rule is a short paraphrase written for this project, page-cited, **unreviewed**. Legend:

- **Type**: `A` mechanical · `B` depends on the stop or on the neighbouring word · `C` a closed
  word list named by the book (matched on the book's own Kufian ayah numbers).
- **Detector**: every rule has one. The two-hamza rules and part of the vowel-on-a-sakin-letter rule
  are found only at the places the farsh table of the longer book lists, because the Qaloun text keeps
  only the result.
- **Tariq**: no rule names one. Book A attests Qaloun without naming a tariq, so every rule is `unspecified`.

| Rule | Arabic name | Family | Type | Detector | Pages (Book A; 92 rules also cite the longer book, see the rule) |
| --- | --- | --- | :-: | :-: | --- |
| `alef_ana_before_hamza` | ألف أنا قبل همزة مفتوحة أو مضمومة | `madd` | B | yes | 23, 24 |
| `alef_ana_before_hamza_kasra` | ألف أنا قبل همزة مكسورة | `madd` | B | yes | 24 |
| `alef_ana_dropped` | حذف ألف أنا وصلا | `madd` | B | yes | 23, 24 |
| `alef_thabita` | الألفات الثابتة وقفا ووصلا | `madd` | C | yes | 23, 24 |
| `madd_alif_lam_mim_imran` | الم الله في فاتحة آل عمران وصلا | `madd` | C | yes | 23 |
| `madd_arid_sukun` | المد العارض للسكون | `madd` | B | yes | 20 |
| `madd_badal` | مد البدل | `madd` | A | yes | 15, 16 |
| `madd_harf_hay_tahar` | الألف في هجاء أحرف حي طهر | `madd` | A | yes | 15, 17, 23 |
| `madd_iwad` | مد العوض | `madd` | A | yes | 15, 16, 17 |
| `madd_lazim_harfi_mukhaffaf` | المد اللازم الحرفي المخفف | `madd` | A | yes | 22, 23 |
| `madd_lazim_harfi_muthaqqal` | المد اللازم الحرفي المثقل | `madd` | A | yes | 22 |
| `madd_lazim_kalimi_mukhaffaf` | المد اللازم الكلمي المخفف | `madd` | C | yes | 21, 22 |
| `madd_lazim_kalimi_muthaqqal` | المد اللازم الكلمي المثقل | `madd` | A | yes | 21 |
| `madd_letter_dropped` | حذف حرف المد لالتقاء الساكنين | `madd` | B | yes | 24 |
| `madd_lin` | مد اللين | `madd` | B | yes | 20, 21 |
| `madd_munfasil` | المد الجائز المنفصل | `madd` | A | yes | 19 |
| `madd_muttasil` | المد الواجب المتصل | `madd` | A | yes | 19 |
| `madd_muttasil_arid` | المد المتصل العارض | `madd` | B | yes | 20 |
| `madd_sila_ha_exception` | كلمات استثنيت من صلة هاء الضمير | `madd` | C | yes | 18, 19, 20 |
| `madd_sila_kubra_ha` | الصلة الكبرى في هاء الضمير | `madd` | A | yes | 19, 20 |
| `madd_sila_kubra_meem` | الصلة الكبرى في ميم الجمع | `madd` | A | yes | 19, 20 |
| `madd_sila_sughra_ha` | الصلة الصغرى في هاء الضمير | `madd` | A | yes | 17, 18, 19 |
| `madd_sila_sughra_meem` | الصلة الصغرى في ميم الجمع | `madd` | A | yes | 17, 18 |
| `madd_tabii` | المد الطبيعي | `madd` | A | yes | 14, 15 |
| `noon_tawkid_khafifa_stop` | الوقف على نون التوكيد الخفيفة المرسومة تنوينا | `madd` | C | yes | 16, 17 |
| `hamza_arayta_tashil` | تسهيل الهمزة الثانية في أرأيت وأرأيتكم وأرأيتم | `hamza` | C | yes | 27 |
| `hamza_double_exception` | استثناءات الهمزتين في كلمة | `hamza` | C | yes | 26, 27 |
| `hamza_double_in_word` | الهمزتان في كلمة | `hamza` | A | yes | 26 |
| `hamza_ibdal_minsaa` | إبدال الهمزة في منسأته | `hamza` | C | yes | 25 |
| `hamza_ibdal_musada` | إبدال الهمزة في مؤصدة | `hamza` | C | yes | 25 |
| `hamza_ibdal_ruya` | إبدال الهمزة في رئيا | `hamza` | C | yes | 25 |
| `hamza_ibdal_saala` | إبدال الهمزة في سأل | `hamza` | C | yes | 25 |
| `hamza_ibdal_yajuj` | إبدال الهمزة ألفا في يأجوج ومأجوج | `hamza` | C | yes | 25 |
| `hamza_istifham_added` | همزة الاستفهام المزيدة في ءامنتم وءأله | `hamza` | C | yes | 27 |
| `hamza_istifham_before_article` | همزة الاستفهام قبل همزة أل التعريف | `hamza` | C | yes | 31 |
| `hamza_nabi` | همز النبي ونحوها | `hamza` | C | yes | 25, 26 |
| `hamza_nabi_exception` | استثناء النبي في موضعي الأحزاب | `hamza` | C | yes | 26 |
| `hamza_two_words_different` | الهمزتان المختلفتان في كلمتين | `hamza` | C | yes | 28, 29 |
| `hamza_two_words_same` | الهمزتان المتفقتان في كلمتين | `hamza` | C | yes | 27, 28 |
| `hamza_wasl_then_qat_in_word` | اجتماع همزة الوصل وهمزة القطع في الكلمة | `hamza` | A | yes | 16 |
| `hamza_waw_huzu_kufu` | همز الواو في هزوا وكفوا | `hamza` | C | yes | 25 |
| `hamzat_wasl_article` | همزة الوصل في أل التعريف | `hamza` | A | yes | 29, 31 |
| `hamzat_wasl_noun` | همزة الوصل في الأسماء | `hamza` | C | yes | 29, 30, 31 |
| `hamzat_wasl_verb` | همزة الوصل في الأفعال | `hamza` | B | yes | 30, 31 |
| `istifham_repeated_first` | الاستفهام المكرر: ما أثبتت همزته في الأول | `hamza` | C | yes | 27 |
| `istifham_repeated_second` | الاستفهام المكرر: ما أثبتت همزته في الثاني | `hamza` | C | yes | 27 |
| `sakin_before_hamzat_wasl` | تحريك الساكن قبل همزة الوصل | `hamza` | B | yes | 31 |
| `alef_tafkhim` | تفخيم الألف | `tafkhim_tarqiq` | B | yes | 32, 35 |
| `alef_tafkhim_after_ra` | تفخيم الألف بعد الراء غير المقللة | `tafkhim_tarqiq` | A | yes | 35 |
| `alef_tarqiq` | ترقيق الألف | `tafkhim_tarqiq` | B | yes | 35 |
| `ghunna_tafkhim` | تفخيم الغنة | `tafkhim_tarqiq` | B | yes | 35 |
| `ghunna_tarqiq` | ترقيق الغنة | `tafkhim_tarqiq` | B | yes | 35 |
| `istiala_rank_1` | المرتبة الأولى من تفخيم الاستعلاء | `tafkhim_tarqiq` | A | yes | 32 |
| `istiala_rank_2` | المرتبة الثانية من تفخيم الاستعلاء | `tafkhim_tarqiq` | A | yes | 32, 33 |
| `istiala_rank_3` | المرتبة الثالثة من تفخيم الاستعلاء | `tafkhim_tarqiq` | A | yes | 32, 33 |
| `istiala_rank_4` | المرتبة الرابعة من تفخيم الاستعلاء | `tafkhim_tarqiq` | A | yes | 32, 33 |
| `lam_jalala_tafkhim` | تفخيم لام لفظ الجلالة | `tafkhim_tarqiq` | B | yes | 34, 35 |
| `lam_jalala_tarqiq` | ترقيق لام لفظ الجلالة | `tafkhim_tarqiq` | B | yes | 34, 35 |
| `ra_jawaz` | جواز الوجهين في راء فرق | `tafkhim_tarqiq` | C | yes | 34 |
| `ra_mutatarrif_jawaz` | جواز الوجهين في الراء المتطرفة | `tafkhim_tarqiq` | C | yes | 34 |
| `ra_mutatarrif_tafkhim` | تفخيم الراء المتطرفة | `tafkhim_tarqiq` | B | yes | 34 |
| `ra_mutatarrif_tarqiq` | ترقيق الراء المتطرفة | `tafkhim_tarqiq` | B | yes | 34 |
| `ra_tafkhim` | تفخيم الراء | `tafkhim_tarqiq` | B | yes | 33, 34 |
| `ra_tarqiq` | ترقيق الراء | `tafkhim_tarqiq` | B | yes | 33, 34 |
| `ya_idafa_fath` | فتح ياء الإضافة قبل الهمزة | `ya_idafa` | B | yes | 45, 46, 47, 48, 49, 50 |
| `ya_idafa_fath_exception` | ياءات الإضافة المفتوحة استثناء | `ya_idafa` | C | yes | 50 |
| `ya_idafa_iskan_before_letter` | ياءات الإضافة الساكنة قبل الحروف | `ya_idafa` | C | yes | 47, 50 |
| `ya_idafa_iskan_exception` | ياءات الإضافة الساكنة استثناء | `ya_idafa` | C | yes | 46, 48, 49, 50 |
| `ya_idafa_maee` | ياء الإضافة في كلمة معي | `ya_idafa` | C | yes | 47 |
| `ya_idafa_rabbi_two_readings` | ياء ربي في فصلت | `ya_idafa` | C | yes | 46, 49 |
| `idgham_kabir_mutamathil` | الإدغام الكبير المتماثل | `idgham_general` | C | yes | 36 |
| `idgham_mutajanisayn` | إدغام المتجانسين | `idgham_general` | A | yes | 36, 37, 38 |
| `idgham_mutamathilayn` | إدغام المتماثلين | `idgham_general` | A | yes | 36 |
| `idgham_mutaqaribayn` | إدغام المتقاربين | `idgham_general` | A | yes | 38 |
| `idgham_naqis` | الإدغام الناقص | `idgham_general` | C | yes | 38, 39 |
| `idgham_bighunna` | الإدغام بغنة | `noon_sakina_tanween` | B | yes | 5, 6 |
| `idgham_bilaghunna` | الإدغام بغير غنة | `noon_sakina_tanween` | B | yes | 5 |
| `idhar_halqi` | الإظهار الحلقي | `noon_sakina_tanween` | B | yes | 4, 5 |
| `idhar_mutlaq` | الإظهار المطلق | `noon_sakina_tanween` | C | yes | 6 |
| `ikhfa_haqiqi` | الإخفاء الحقيقي | `noon_sakina_tanween` | B | yes | 7, 8 |
| `iqlab` | الإقلاب | `noon_sakina_tanween` | B | yes | 7 |
| `idgham_shafawi` | الإدغام الشفوي | `mim_sakina` | B | yes | 9 |
| `idhar_shafawi` | الإظهار الشفوي | `mim_sakina` | B | yes | 9, 10 |
| `ikhfa_shafawi` | الإخفاء الشفوي | `mim_sakina` | B | yes | 9 |
| `ghunna_mushaddad` | غنة النون والميم المشددتين | `ghunna` | A | yes | 11 |
| `qalqala` | القلقلة | `qalqala` | A | yes | 44 |
| `lam_qamariya` | اللام القمرية | `lam_taarif` | A | yes | 13 |
| `lam_shamsiya` | اللام الشمسية | `lam_taarif` | A | yes | 12, 13 |
| `imala_har` | الإمالة في هار | `imala_taqlil` | C | yes | 35 |
| `taqlil_tawrat` | التقليل في التوراة | `imala_taqlil` | C | yes | 35 |
| `ya_zaida_joined_kept` | الياء الزائدة المثبتة وصلا المحذوفة وقفا | `ya_zaida` | C | yes | — (Nabhan 80, 81) |
| `ya_zaida_kept_both` | الياء الزائدة المثبتة وصلا ووقفا | `ya_zaida` | C | yes | — (Nabhan 80, 81) |
| `ya_zaida_two_ways` | الياء الزائدة بالوجهين وصلا | `ya_zaida` | C | yes | — (Nabhan 80, 81) |
| `waqf_ayyuh` | الوقف على أيه بالهاء | `waqf` | C | yes | — (Nabhan 82-86) |
| `waqf_maqtu` | الكلمتان المقطوعتان رسما | `waqf` | C | yes | — (Nabhan 82-86) |
| `waqf_split_word` | الكلمة المجزأة رسما | `waqf` | C | yes | — (Nabhan 82-86) |
| `waqf_ta_open` | الوقف على تاء التأنيث المبسوطة | `waqf` | C | yes | — (Nabhan 82-86) |

| Family | Rules | What it covers |
| --- | ---: | --- |
| `madd` | 25 | natural, badal, 'iwad, muttasil, munfasil, 'arid, lin, lazim, sila of the ha and meem, fixed alefs, alef of ana, light tawkid noon, الم الله |
| `hamza` | 22 | replaced hamzas, prophet words, two hamzas, repeated interrogatives, hamzat al-wasl, wasl then qat' in one word, أرأيت, hamza before the article |
| `tafkhim_tarqiq` | 17 | ra, lam of Allah, alef (also after ra), ghunna, the four ranks of the isti'la letters |
| `ya_idafa` | 6 | open and closed first-person ya, `معي`, `ربي` of Fussilat |
| `waqf` | 4 | stops that depend on the rasm: open ta, words written apart, `أيه`, a split word (from the longer book only) |
| `ya_zaida` | 3 | the zaida ya: kept when joined, kept or dropped, kept always (from the longer book only) |
| `idgham_general` | 5 | identical, same-place and close letters, naqis, the great idgham |
| `noon_sakina_tanween` | 6 | idhar, idgham, iqlab, ikhfa |
| `mim_sakina`, `lam_taarif`, `imala_taqlil`, `qalqala` | 3 · 2 · 2 · 1 | shafawi rules, article lam, taqlil and imala, qalqala |
| `ghunna` | 1 | geminated noon and meem |

**What the detectors read.** A maddah marks the long madds; a superscript alef marks a madd alef;
a small waw or yeh on a ha marks the sila; a sakin noon or meem before idgham, ikhfa and iqlab
letters has no sukun; an alef inserted between two hamzas is a superscript alef; the open
first-person ya is spelled with a fatha and the closed one with the yeh barree; hamzat al-wasl has
three different marks.

## 8. Data and numbering

| Datum | Origin | Guard |
| --- | --- | --- |
| Quran text | KFGQPC Qaloun via Qur'anpedia (`risan/quran-json`, commit `6523a9ad…`), 6,214 ayat, **bundled** in `src/wirdi_mcp/quran/snapshot/` (CC BY-SA 4.0, see [NOTICE](src/wirdi_mcp/quran/snapshot/NOTICE.md)) | SHA-256 checked on every call; never modified |
| 559-page layout and mapping resolver | Same snapshot (page map derived from the King Fahd mushaf images; resolver code of the Wirdi AI project, trimmed schemas, short public notes) | SHA-256 checked; `verified_against_edition` |
| Rules | `knowledge/rules/*/1.json` | `manifest.json` pins every file; one altered byte gives `INTEGRITY_FAILURE` |
| Books | PDFs placed locally in `docs/` | Never committed; only paraphrased rules with a page citation are |

**Licences.** The code, tests, scripts and docs are MIT ([LICENSE](LICENSE)). The folder
`src/wirdi_mcp/quran/snapshot/` keeps its own terms ([LICENSE-DATA](src/wirdi_mcp/quran/snapshot/LICENSE-DATA.md)):
the Quran text is CC BY-SA 4.0 with credit to Qur'anpedia.net and the dump version; ShareAlike
applies to that data, not to the code that reads it. The books themselves are never in the repository.

**Two numberings meet here.**

| | Qaloun count | Kufian count |
| --- | --- | --- |
| Used by | the corpus, the tools, the application | the place numbers of Book A |
| Ayat | 6,214 | 6,236 |
| Kept in the corpus as | the ayah number | `number_in_hafs` |
| Pages | 559 (application) | 604 (Hannibal) |

78 Qaloun ayat gather two Kufian numbers and 59 Kufian ayat are split, touching 59 surahs. In
Al-Baqara: Qaloun 2:5 = Kufian 2:6, Qaloun 2:7 = 2:8. Convert with `resolve_source_mapping`. Pages are
never compared by number, only through the verse.

## 9. Sources and where they disagree

| Source | Role | State |
| --- | --- | --- |
| **Book A**, *أحكام رواية قالون عن نافع المدني* (51 pp.) | The base of 90 of the 97 rules; Qaloun, names no tariq | Citations checked on the page images; inconsistent in places (below) |
| **Nabhan**, *الثمر اليانع في أصول رواية قالون عن نافع* (214 pp.) | The longer book Book A digests; names Abu Nashit (p.111 only). Second citation of 92 rules, sole source of the 3 `ya_zaida` rules | Pages read on their images; local, never committed; see [BOOK_NABHAN_EVALUATION](docs/BOOK_NABHAN_EVALUATION.md) |

Book A has an unknown licence (it is never committed). Its text layer is raw (inverted lam-alef ligatures).

**Where Book A contradicts itself or the corpus** (each case is in the rule limits and in
[BOOK_A_COVERAGE](docs/BOOK_A_COVERAGE.md); none is arbitrated):

| Case | What happens |
| --- | --- |
| `فألقه` (p.19 against p.20), `يأته` | Both readings are in `variants` |
| `آلآن` (p.21) | Three readings in `variants` |
| Ya'at lists (p.46 against p.49) | Four place numbers differ; each word was looked up in the corpus and the retained place is documented. The longer source book shows two are Book A's own slips and the others inherited |
| `معي` (p.47) | The book's sentence is the reverse of the corpus spelling and of its own classes, and differs from the longer book it digests (Nabhan p.79); each occurrence reports what the corpus spells |
| Plural meem before ba and meem (1,314 places) | Sila by the general wording of p.17; its exclusion of ikhfa/idgham shafawi is an **inference**, written in both annotations |
| Madd lengths | A reviewer proposes 2 or 4 (munfasil) and 4 (muttasil); Book A says 2, 3 or 4 and 3 or 4. Open |

## 10. What is not covered

- Most waqf and ibtida rules (the chosen stops, rawm, ishmam, pp.87-98 of the longer book) and waqf
  signs inside an ayah: the engine stops only at an ayah end. Only the closed lists that depend on
  the rasm are built (`waqf_*`).
- The vowel of sakin letters before hamzat al-wasl, and two hamzas in two words, **outside** the
  places the farsh table lists (19 and 82 places the corpus shows).
- The default closed ya before an ordinary letter, beyond the seven named examples.
- Everything Book A does not say (it is a 51-page summary).

[BOOK_A_COVERAGE](docs/BOOK_A_COVERAGE.md) lists each section of the book and its state.

## 11. Tests

```bash
.venv/bin/python -m pytest                                          # everything, on the bundled snapshot
WIRDI_TEST_SOURCE_ROOT=/abs/wirdi-Ai .venv/bin/python -m pytest    # + checks against the original files: 322 tests
```

- **Synthetic and stdio**: synthetic fixtures modelled on the books' examples, real stdio subprocess tests, the
  README and APPLY.json consistency checks, tamper tests.
- **Real corpus (bundled)**: every single-ayah selection in both modes, all 559 pages, the closed word lists
  (each must hit exactly the places the book names), and every request of `docs/APPLY.json`.

## 12. Repository layout and scripts

```
src/wirdi_mcp/
  server.py, config.py        entry point and configuration
  domain/                     typed contracts (Pydantic): annotations, statuses, references
  quran/                      checksum-pinned, read-only access to the Wirdi AI files
  mapping/                    the mapping authority (Qaloun <-> Hafs)
  knowledge/                  rule registry (hash-pinned) and local page store (fail-closed)
  tajwid/                     tokenizer and detectors: madd, hamza, tafkhim, idgham, yaat,
                              lexicon (word lists), letters (static tables), engine, service
  tools/                      the 12 MCP tools and their contracts
knowledge/rules/              97 rule records + manifest.json     (committed)
knowledge/sources/            edition metadata only               (no book text)
knowledge/validation/         empty, ready for a reviewer's records
scripts/                      rule generation, manifest, audit, page store, local check
tests/                        unit and integration tests
docs/                         design, audits, reports, guides and APPLY.json (PDFs are git-ignored)
```

The commands that use the scripts are in [section 3](#3-key-commands).

## 13. What needs a human

1. **A named, qualified reviewer.** Without one, nothing moves beyond `candidate`; the validation
   store is ready and empty.
2. **Licences** of the books (the code and bundled data are licensed, see section 8), and whether the paraphrased records may stay in the
   repository.
3. **Which tariq?** Book A names none; the corpus does not attest one either.
4. **Display in version 1**: label unreviewed candidates, or show nothing until a reviewer approves?
5. **Arbitration** of the divergences in section 9, with the reviewer.
6. **Integration into Wirdi AI** (not started): [INTEGRATION](docs/INTEGRATION.md).

## 14. Documentation index

| Document | Contents |
| --- | --- |
| [APPLY.json](docs/APPLY.json) | One ready-to-paste JSON request per tool, with the expected result; checked by a test |
| [NoteImportant](docs/NoteImportant.md) | Inspector setup, data origin, every test done and its analysis |
| [TESTING_GUIDE](docs/TESTING_GUIDE.md) | A request per rule family and what to check |
| [BOOK_A_COVERAGE](docs/BOOK_A_COVERAGE.md) | Each Book A section, its rules, its state and the page contradictions |
| [MCP_TOOLS](docs/MCP_TOOLS.md) | Tool contracts, statuses, reading context, failure semantics |
| [TAJWID_ENGINE](docs/TAJWID_ENGINE.md) | Rule, detector, annotation and review, kept separate |
| [RULE_AUDIT](docs/RULE_AUDIT.md) | Per-rule counts over the whole corpus |
| [ARCHITECTURE](docs/ARCHITECTURE.md), [SOURCE_AUDIT](docs/SOURCE_AUDIT.md) | Boundaries, reference identity, the corpus and its checksums |
| [DECISIONS](docs/DECISIONS.md) | Design decisions |
| [BOOK_NABHAN_EVALUATION](docs/BOOK_NABHAN_EVALUATION.md) | Assessment of a second, longer Qaloun book: what it settles in Book A and what it could add |
| [INTEGRATION](docs/INTEGRATION.md) | The planned client contract for Wirdi AI |

The official [`mcp` Python SDK](https://github.com/modelcontextprotocol/python-sdk) is pinned to
2.3.0; this project uses its `MCPServer` API, not the separate `fastmcp` package.
