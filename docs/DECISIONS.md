# Decisions taken autonomously

Applied from the mission defaults; revisit each with the project owner.

1. **Reviewer:** none named. No annotation or rule may reach `scholarly_verified`; the
   highest status emitted is `candidate`.
2. **Transmission path:** Book A names no tariq, so every rule is `tariq=unspecified` and the
   corpus keeps `tariq=unspecified`. Applying the rules to the corpus is a documented hypothesis.
3. **Divergent or ambiguous sources:** listed in `variants` and in the rule limits; no silent
   choice.
4. **Git hygiene:** `*.pdf` and page images are ignored globally (including `*.png`/`*.jpg`).
5. **Scope:** the server rests on Book A only. The coloured-mushaf extraction was tried and
   dropped; Book B is not used, and its code, models and citations were removed.
6. **Source divergence:** Book A states some words two ways (pp.19-20, 46-50); the rule records keep both and do not choose.
7. **Detector input:** the corpus spells the sakin noon/mim before idgham, ikhfa and
    iqlab letters without a sukun and signals iqlab with a small high meem, so detectors
    classify by the following letter and recognise bare noon/mim as sakin.
8. **Candidate default:** `include_candidates` defaults to true because no reviewed
    annotation exists; with false the tools return no annotation and say why.
9. **Book A completion (0.6.0):** Book A is a Qaloun source that does not name Abu Nashit, so
    the 65 new rules carry `tariq: "unspecified"`. Word lists keep the book's own words and are
    matched against the Kufian number of the ayah (`number_in_hafs`), the numbering the book's
    printed copy uses. Where the book permits several readings the detector lists them in
    `variants` and does not choose.
10. **Not detected on purpose:** two hamzas in two words (the Qaloun text keeps only the result),
    the default closed ya before ordinary letters (indistinguishable from an ordinary final
    yeh), joining a wasl and a qat' hamza in one word (needs morphology). Their rules are
    readable or listed in `docs/BOOK_A_COVERAGE.md`; nothing is invented to fill them.
11. **Corpus orthography is evidence:** the corpus marks sila with small waw/yeh, fathatan on an
    alef, assimilation with a shadda on the second letter, hamzat al-wasl with three signs, the
    open ya with a fatha and the closed one with the yeh barree. Detectors read those signs and
    say so in their notes and limitations.

12. **Self-contained snapshot (2026-10-31):** the Quran text, the 559-page map, the mapping
    resolver and three short public notes are bundled in `src/wirdi_mcp/quran/snapshot/`, pinned
    by SHA-256 (`bundled` section of `source_manifest.json`). `schemas.py` is trimmed to
    `MappingOut` and `PassageReference`; a test shows identical mapping output to the original on
    all 6,214 selections. `WIRDI_AI_ROOT` stays an optional override that verifies the original
    files. Code is MIT; the data folder is CC BY-SA 4.0 with Qur'anpedia credit.
16. **Second book, cross-check only (2026-11-01):** the longer Qaloun book Book A digests
    (Nabhan, `docs/BOOK_NABHAN_EVALUATION.md`) is used to check Book A, not as a cited source. Its
    findings are written into notes and limits (the معي sentence, the Sad and al-Ahqaf slips), and it
    names Abu Nashit, which is recorded and applied to no rule. Citing it per rule and reading its farsh
    tables are left to a later decision.
17. **Second book as a verification source (2026-11-01):** after reading the usul pages on their
    images, 92 rules carry a second citation to Nabhan (« same text as Book A »), the tariq stays
    `unspecified`, and the topics Book A lacks that the corpus can show were added (`ya_zaida_*`,
    `hamza_istifham_before_article`). Waqf, madd combinations and the farsh tables remain open.
