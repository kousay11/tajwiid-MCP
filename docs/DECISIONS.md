# Decisions taken autonomously

Applied from the mission defaults; revisit each with the project owner.

1. **Reviewer:** none named. No annotation or rule may reach `verified` /
   `scholarly_verified`; the highest status emitted is `cross_checked`.
2. **Transmission path:** the Abu Nashit attestation of the Hannibal mushaf (page م1)
   and of book B is a documented hypothesis. The corpus keeps `tariq=unspecified`.
3. **Mushaf reading context:** annotations derived from the coloured mushaf are
   labelled `waqf` (end of verse and waqf signs).
4. **Divergent or ambiguous sources:** status `conflict`; no silent choice.
5. **Manifest drift (J0):** only the `arabic.py` and `schemas.py` hashes were updated,
   after the complete real-source conformance passed. See `SOURCE_AUDIT.md`.
6. **Git hygiene:** `*.pdf`, page images and mushaf-derived data are ignored globally
   (including `*.png`/`*.jpg`) before the first commit.
7. **Mushaf pilot (J4): NO-GO.** Blob to letter attachment is not computable without glyph
   recognition, legend colours do not separate on the text, recall and ornament masking
   are inadequate. The full extraction (J5) was skipped; see `PILOT_REPORT.md`.
8. **Rule tariq:** rule records cite book B (Abu Nashit) or only book A; a rule backed by
   both is marked `abu_nashit`, one backed by book A alone `unspecified`. Applying either to
   the corpus is the documented hypothesis from decision 2.
9. **Source divergence:** books A (pp.5-6) and B (p.58) classify the completeness of the
   idgham with ghunna differently. The rule record states both and does not choose.
10. **Detector input:** the corpus spells the sakin noon/mim before idgham, ikhfa and
    iqlab letters without a sukun and signals iqlab with a small high meem, so detectors
    classify by the following letter and recognise bare noon/mim as sakin.
11. **Candidate default:** `include_candidates` defaults to true because no reviewed
    annotation exists; with false the tools return no annotation and say why.
12. **Book A completion (0.6.0):** Book A is a Qaloun source that does not name Abu Nashit, so
    the 65 new rules carry `tariq: "unspecified"`. Word lists keep the book's own words and are
    matched against the Kufian number of the ayah (`number_in_hafs`), the numbering the book's
    printed copy uses. Where the book permits several readings the detector lists them in
    `variants` and does not choose.
13. **Not detected on purpose:** two hamzas in two words (the Qaloun text keeps only the result),
    the default closed ya before ordinary letters (indistinguishable from an ordinary final
    yeh), joining a wasl and a qat' hamza in one word (needs morphology). Their rules are
    readable or listed in `docs/BOOK_A_COVERAGE.md`; nothing is invented to fill them.
14. **Corpus orthography is evidence:** the corpus marks sila with small waw/yeh, fathatan on an
    alef, assimilation with a shadda on the second letter, hamzat al-wasl with three signs, the
    open ya with a fatha and the closed one with the yeh barree. Detectors read those signs and
    say so in their notes and limitations.

