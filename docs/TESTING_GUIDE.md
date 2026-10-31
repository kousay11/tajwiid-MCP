# Testing guide: try every rule family

**Every request below, and one for each tool, is also in [APPLY.json](APPLY.json) ready to paste.**

All requests are MCP tool calls. Use the MCP Inspector or any client; the arguments below are
the JSON the tool receives. Set `WIRDI_AI_ROOT` to your Wirdi AI checkout first.

```bash
WIRDI_AI_ROOT=/home/najjar/Documents/Me/wirdi-Ai npx @modelcontextprotocol/inspector \
  .venv/bin/wirdi-mcp
```

A selection is `{"start": {...reference...}, "end_ayah": N}`. Selections here use the Qaloun count
of the corpus (Kufian numbers appear in `number_in_hafs`, and Book A quotes places in those). The reference below is the Qaloun
corpus reference; only `surah` and `ayah` change:

```json
{"corpus_id": "wirdi-ai:quranpedia:qalun",
 "corpus_version": "sha256:ece0a2b0efe44d496211c595d0a34f495413bc93f78fba8095a666e2048d1303",
 "numbering_system": "wirdi-ai:qalun-6214", "riwaya": "qaloun", "tariq": "unspecified",
 "surah": 2, "ayah": 1}
```

## 1. See what exists

- `list_tajwid_rules {}`: 81 rules, each with `family` and `has_detector`. Pass `{"family": "madd"}`
  to filter. Families: `madd`, `hamza`, `tafkhim_tarqiq`, `imala_taqlil`, `idgham_general`,
  `ya_idafa` and the first-release families `qalqala`, `noon_sakina_tanween`, `mim_sakina`,
  `ghunna`, `lam_taarif`.
- `get_tajwid_rule {"rule_id": "madd_munfasil", "version": "1"}`: the paraphrased rule, its
  conditions, exceptions, limitations and Book A page.

## 2. Analyse a passage

`analyze_qaloun_tajwid` takes `selection`, `reading_context` (`{"mode": "waqf"}` or `{"mode": "wasl"}`),
and optionally `families`, `rule_ids`, `limit` (1 to 500) and `offset`. Each annotation has the
rule, the exact text range (`anchor`), the note, the app page, the book citation, and
`variants` when the book permits several readings.

| To see | Selection | Filter |
| --- | --- | --- |
| Isolated letters at a surah opening (`madd_harf_hay_tahar`, lazim harfi) | 2:1 to 2:1, 19:1, 42:1 | `{"families": ["madd"]}` |
| Connected and separated madd with their lengths | 2:1 to 2:7 | `{"rule_ids": ["madd_muttasil", "madd_munfasil"]}` |
| Madd 'arid (waqf only) | 1:1 to 1:7 | `{"rule_ids": ["madd_arid_sukun"]}` |
| Madd lin (waqf only) | 90:8 to 90:9 | `{"rule_ids": ["madd_lin"]}` |
| Pronoun ha and plural meem lengthening | 2:1 to 2:30 | `{"rule_ids": ["madd_sila_sughra_ha", "madd_sila_kubra_meem"]}` |
| Hamzat al-wasl | 1:1 to 1:7 | `{"rule_ids": ["hamzat_wasl_article", "hamzat_wasl_verb"]}` |
| Two hamzas in one word | 6:20 to 6:20 | `{"rule_ids": ["hamza_double_in_word"]}` |
| Hamza of Yajuj and Majuj (Qaloun count 90, Kufian 94) | 18:90 to 18:90 | `{"rule_ids": ["hamza_ibdal_yajuj"]}` |
| Heavy and light ra, lam of Allah | 1:1 to 1:7 | `{"families": ["tafkhim_tarqiq"]}` |
| Taqlil of al-Tawrat | 3:1 to 3:4 | `{"rule_ids": ["taqlil_tawrat"]}` |
| General idgham | 2:15 to 2:20 | `{"families": ["idgham_general"]}` |
| Ya'at al-idafa | 2:29 to 2:40 | `{"families": ["ya_idafa"]}` |

`reading_context` `wasl` makes the last word of the selection depend on the next ayah: pass
`"following": {…reference of the next ayah…}` or those positions come back under `unresolved`.

## 3. Summaries and pages

- `summarize_tajwid {"surah": 18, "reading_context": {"mode": "waqf"}, "families": ["madd"]}`:
  counts per rule and per ayah.
- `analyze_app_page {"page": 263, "reading_context": {"mode": "waqf"}, "families": ["hamza"]}`:
  the ayat that begin on that page of the 559-page layout.

## 4. Letters

`get_letter_properties {"letters": ["ق", "ء", "ر"]}` returns the place of articulation and the
characteristics of each letter (Book A pp.40-45). One base letter per entry, 1 to 29 entries.

## 5. What to check yourself

1. Pick 10 ayat you know. For each annotation, is the letter range right and is the rule right?
2. Look at `variants`: does the list match what you teach (lengths, readings)?
3. Look at `unresolved` and `skipped`: are the cases left out the ones that really need context?
4. Look for rules you expected and did not get. `docs/BOOK_A_COVERAGE.md` says which Book A rules
   have no detector and why.
5. Proofread the rule records in `knowledge/rules/` against the cited Book A pages.

Everything returned is `candidate`: no reviewer has confirmed anything.
